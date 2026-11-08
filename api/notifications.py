import logging
import requests
from django.utils import timezone
from .models import (
    UserDevice, NotificationLog, FavoriteTeam, ScoutList,
    Fixture, Player, Team
)

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_expo_push_notification(tokens, title, body, data=None):
    """
    Expo Push Notification API'sine HTTP POST isteği gönderir.
    tokens: list of Expo push token strings (örn: ['ExponentPushToken[...]'])
    """
    if not tokens:
        return {"status": "no_tokens", "sent": 0}

    valid_tokens = [t for t in tokens if isinstance(t, str) and (t.startswith('ExponentPushToken[') or t.startswith('ExpoPushToken['))]
    if not valid_tokens:
        logger.info(f"[PushNotification] Geçerli token bulunamadı: {tokens}")
        return {"status": "invalid_tokens", "sent": 0}

    messages = []
    for token in valid_tokens:
        messages.append({
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
            "data": data or {},
            "priority": "high",
            "channelId": "superlig-match-alerts",
        })

    try:
        response = requests.post(
            EXPO_PUSH_URL,
            json=messages,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Content-Type": "application/json",
            },
            timeout=8
        )
        res_json = response.json() if response.status_code == 200 else {}
        logger.info(f"[PushNotification] {len(messages)} cihaza bildirim yollandı. Status: {response.status_code}")
        return {"status": "success", "sent": len(messages), "response": res_json}
    except Exception as e:
        logger.error(f"[PushNotification] Hata: {e}")
        return {"status": "error", "message": str(e), "sent": 0}


def dispatch_match_goal_notification(fixture, event_data, target_user=None):
    """
    Canlı maçta gol olduğunda hem veritabanına NotificationLog kaydeder
    hem de ilgili takımı veya futbolcuyu favorileyen kullanıcılara Push bildirimi basar.
    """
    scorer_name = event_data.get('scorer') or 'Bilinmeyen Oyuncu'
    assist_name = event_data.get('assist')
    minute = event_data.get('minute') or ''
    is_pen = event_data.get('is_penalty')
    is_og = event_data.get('is_own_goal')

    suffix = " (Penaltı)" if is_pen else (" (Kendi Kalesine)" if is_og else "")
    min_str = f" ({minute}')" if minute else ""
    title = f"⚽ GOL! {scorer_name}{suffix}{min_str}"

    h_score = fixture.home_score if fixture.home_score is not None else 0
    a_score = fixture.away_score if fixture.away_score is not None else 0
    score_str = f"{fixture.home_team.name} {h_score} - {a_score} {fixture.away_team.name}"
    body = score_str
    if assist_name and not is_og:
        body += f" • Asist: {assist_name}"

    payload = {
        "fixture_id": fixture.id,
        "type": "GOAL",
        "home_team": fixture.home_team.name,
        "away_team": fixture.away_team.name,
        "home_score": fixture.home_score,
        "away_score": fixture.away_score,
        "scorer": scorer_name,
        "assist": assist_name,
        "minute": minute,
        "timestamp": timezone.now().isoformat()
    }

    # Hedef kullanıcıları belirle
    user_ids = set()
    if target_user:
        user_ids.add(target_user.id)
    else:
        # 1. Takımı favorileyenler
        team_favs = FavoriteTeam.objects.filter(
            team__in=[fixture.home_team, fixture.away_team],
            notify_goals=True
        ).values_list('user_id', flat=True)
        user_ids.update(team_favs)

        # 2. Golü atan veya asisti yapan futbolcuyu favorileyenler
        player_favs = ScoutList.objects.filter(
            player__name__icontains=scorer_name.split()[-1] if scorer_name else '',
            notify_goals=True
        ).values_list('user_id', flat=True)
        user_ids.update(player_favs)

        if assist_name:
            assist_favs = ScoutList.objects.filter(
                player__name__icontains=assist_name.split()[-1],
                notify_assists=True
            ).values_list('user_id', flat=True)
            user_ids.update(assist_favs)

    # Bildirim kutusu kayıtları (NotificationLog)
    logs_to_create = []
    if user_ids:
        for u_id in user_ids:
            logs_to_create.append(NotificationLog(
                user_id=u_id,
                title=title,
                body=body,
                notification_type='GOAL',
                related_fixture=fixture,
                related_team=fixture.home_team if fixture.home_team_id else None,
                data_payload=payload
            ))
    else:
        # Genel sistem bildirimi (misafir kullanıcılar da genel inbox görebilsin)
        logs_to_create.append(NotificationLog(
            user=None,
            title=title,
            body=body,
            notification_type='GOAL',
            related_fixture=fixture,
            related_team=fixture.home_team if fixture.home_team_id else None,
            data_payload=payload
        ))

    NotificationLog.objects.bulk_create(logs_to_create)

    # Push Token'ları bul
    if user_ids:
        tokens = list(UserDevice.objects.filter(
            user_id__in=user_ids,
            is_active=True
        ).values_list('expo_push_token', flat=True))
    else:
        # Test veya genel broadcast durumunda tüm aktif tokenlar
        tokens = list(UserDevice.objects.filter(
            is_active=True
        ).values_list('expo_push_token', flat=True))

    push_res = send_expo_push_notification(tokens, title, body, payload)
    return {
        "title": title,
        "body": body,
        "payload": payload,
        "recipients_count": len(user_ids),
        "push_result": push_res
    }


def dispatch_lineup_notification(fixture, player, team, target_user=None):
    """
    Favori oyuncu ilk 11'de başladığında bildirim gönderir.
    """
    opponent = fixture.away_team if team.id == fixture.home_team_id else fixture.home_team
    title = f"📋 İlk 11 Açıklandı: {player.name}"
    body = f"{player.name} bu akşam {team.name} - {opponent.name} derbisinde ilk 11'de sahaya çıkıyor!"

    payload = {
        "fixture_id": fixture.id,
        "type": "LINEUP",
        "player_id": player.id,
        "player_name": player.name,
        "team_name": team.name,
        "timestamp": timezone.now().isoformat()
    }

    user_ids = set()
    if target_user:
        user_ids.add(target_user.id)
    else:
        fav_users = ScoutList.objects.filter(
            player=player,
            notify_starting_11=True
        ).values_list('user_id', flat=True)
        user_ids.update(fav_users)

        team_fav_users = FavoriteTeam.objects.filter(
            team=team,
            notify_lineups=True
        ).values_list('user_id', flat=True)
        user_ids.update(team_fav_users)

    # Kayıt
    if user_ids:
        for u_id in user_ids:
            NotificationLog.objects.create(
                user_id=u_id,
                title=title,
                body=body,
                notification_type='LINEUP',
                related_fixture=fixture,
                related_player=player,
                related_team=team,
                data_payload=payload
            )
    else:
        NotificationLog.objects.create(
            user=None,
            title=title,
            body=body,
            notification_type='LINEUP',
            related_fixture=fixture,
            related_player=player,
            related_team=team,
            data_payload=payload
        )

    tokens = list(UserDevice.objects.filter(is_active=True).values_list('expo_push_token', flat=True))
    if user_ids:
        tokens = list(UserDevice.objects.filter(user_id__in=user_ids, is_active=True).values_list('expo_push_token', flat=True))

    push_res = send_expo_push_notification(tokens, title, body, payload)
    return {"title": title, "body": body, "push_result": push_res}
