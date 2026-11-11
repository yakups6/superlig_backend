from django.core.management.base import BaseCommand
from api.integrations import TransfermarktScraper


class Command(BaseCommand):
    help = "Transfermarkt ve Mackolik uzerinden guncel Super Lig aktif kadrolarini diff algoritmasiyla senkronize eder."

    def add_arguments(self, parser):
        parser.add_argument("--teams", action="store_true", help="Sadece Super Lig kuluplerini listele/dogrula")
        parser.add_argument("--transfers", action="store_true", help="Sadece Super Lig transferlerini dondur")
        parser.add_argument("--squads", action="store_true", help="Tum 18 kulubun guncel kadrolarini diff ile senkronize et")

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("[INFO] Canli Super Lig senkronizasyonu baslatiliyor..."))

        do_all = not (options["teams"] or options["transfers"] or options["squads"])

        if do_all or options["teams"]:
            teams = TransfermarktScraper.scrape_super_lig_teams()
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(teams)} Super Lig kulubu aktif."))

        if do_all or options["squads"]:
            self.stdout.write("Canli kadrolar cekiliyor ve Kadro Farki (Diff) uygulaniyor...")
            summary = TransfermarktScraper.sync_live_squads_with_diff()
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] {summary.get('teams_synced', 0)} takim, "
                    f"{summary.get('active_players_upserted', 0)} aktif oyuncu senkronize edildi; "
                    f"{summary.get('detached_to_legends', 0)} ayrilan + {summary.get('non_sl_swept', 0)} lig disi -> Eski Oyuncular; "
                    f"{len(summary.get('intra_league_transfers', []))} lig ici transfer; "
                    f"Sofascore={summary.get('sofascore_status')}"
                )
            )

        if do_all or options["transfers"]:
            transfers = TransfermarktScraper.scrape_super_lig_transfers()
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(transfers)} transfer kaydi korundu."))

        self.stdout.write(self.style.SUCCESS("[DONE] Senkronizasyon tamamlandi!"))
