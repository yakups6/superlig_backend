# -*- coding: utf-8 -*-
from decimal import Decimal
from datetime import date


def get_transfers_list(teams_map):
    gs = teams_map["GS"]
    fb = teams_map["FB"]
    bjk = teams_map["BJK"]
    ts = teams_map["TS"]
    amed = teams_map["AMD"]
    ibfk = teams_map.get("İBFK")
    alanya = teams_map.get("ALN")
    rize = teams_map.get("RİZ")
    kasimpasa = teams_map.get("KAS")
    kocaeli = teams_map.get("KOC")
    gaziantep = teams_map.get("GFK")
    eyup = teams_map.get("EYÜ")

    return [
        # =========================================================================
        # 1. 2026/2027 GÜNCEL SEZON TRANSFERLERİ (BU SEZON)
        # =========================================================================

        # --- GALATASARAY (Gelenler - 2026/2027) ---
        {
            "player_name": "Victor Osimhen", "pos": "Santrafor", "age": 27, "val": Decimal("65000000"),
            "from_club": ("SSC Napoli", "NAP", "Napoli", "Serie A", "https://upload.wikimedia.org/wikipedia/commons/2/28/S.S.C._Napoli_logo.svg"),
            "to_team": gs, "contract": "LOAN", "fee": Decimal("0"),
            "date": date(2026, 9, 2), "details": "SSC Napoli -> Galatasaray - Kiralık", "season_name": "2026/2027"
        },
        {
            "player_name": "Rafael Leão", "pos": "Sol Kanat", "age": 27, "val": Decimal("40000000"),
            "from_club": ("AC Milan", "MIL", "Milano", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/5.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("38000000"),
            "date": date(2026, 8, 15), "details": "AC Milan -> Galatasaray - 38.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Lesley Ugochukwu", "pos": "Ön Libero", "age": 22, "val": Decimal("22000000"),
            "from_club": ("Chelsea FC", "CHE", "Londra", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/631.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("22000000"),
            "date": date(2026, 8, 30), "details": "Chelsea FC -> Galatasaray - 22.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Wilfried Singo", "pos": "Sağ Bek", "age": 25, "val": Decimal("20000000"),
            "from_club": ("AS Monaco", "ASM", "Monaco", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/162.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("20000000"),
            "date": date(2026, 8, 26), "details": "AS Monaco -> Galatasaray - 20.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "El Chadaille Bitshiabu", "pos": "Stoper", "age": 21, "val": Decimal("18000000"),
            "from_club": ("RB Leipzig", "RBL", "Leipzig", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/23826.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("18000000"),
            "date": date(2026, 7, 25), "details": "RB Leipzig -> Galatasaray - 18.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Aleksey Batrakov", "pos": "On Numara", "age": 21, "val": Decimal("28000000"),
            "from_club": ("Lokomotiv Moskova", "LOK", "Moskova", "Premier Liga", "https://tmssl.akamaized.net/images/wappen/head/932.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("15000000"),
            "date": date(2026, 8, 18), "details": "Lokomotiv Moskova -> Galatasaray - 15.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Leroy Sané", "pos": "Sağ Kanat", "age": 30, "val": Decimal("15000000"),
            "from_club": ("Bayern Münih", "FCB", "Münih", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/27.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("15000000"),
            "date": date(2026, 8, 22), "details": "Bayern Münih -> Galatasaray - 15.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Renato Nhaga", "pos": "Merkez Orta Saha", "age": 19, "val": Decimal("6000000"),
            "from_club": ("OGC Nice", "NIC", "Nice", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/417.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("6000000"),
            "date": date(2026, 8, 10), "details": "OGC Nice -> Galatasaray - 6.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Deniz Gül", "pos": "Santrafor", "age": 22, "val": Decimal("10000000"),
            "from_club": ("FC Porto", "POR", "Porto", "Liga Portugal", "https://tmssl.akamaized.net/images/wappen/head/720.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("5000000"),
            "date": date(2026, 8, 12), "details": "FC Porto -> Galatasaray - 5.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Mario Lemina", "pos": "Ön Libero", "age": 33, "val": Decimal("3500000"),
            "from_club": ("Wolverhampton Wanderers", "WOL", "Wolverhampton", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/543.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("3500000"),
            "date": date(2026, 8, 20), "details": "Wolverhampton -> Galatasaray - 3.50M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "İlkay Gündoğan", "pos": "Merkez Orta Saha", "age": 36, "val": Decimal("1500000"),
            "from_club": ("Manchester City", "MCI", "Manchester", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/281.png"),
            "to_team": gs, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 8, 1), "details": "Manchester City -> Galatasaray - Bedelsiz", "season_name": "2026/2027"
        },
        {
            "player_name": "Uğurcan Çakır", "pos": "Kaleci", "age": 30, "val": Decimal("13000000"),
            "from_team": ts, "to_team": gs, "contract": "PERMANENT", "fee": Decimal("13000000"),
            "date": date(2026, 8, 14), "details": "Trabzonspor -> Galatasaray - 13.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Eren Elmalı", "pos": "Sol Bek", "age": 26, "val": Decimal("5000000"),
            "from_team": ts, "to_team": gs, "contract": "PERMANENT", "fee": Decimal("5000000"),
            "date": date(2026, 8, 16), "details": "Trabzonspor -> Galatasaray - 5.00M € Bonservis", "season_name": "2026/2027"
        },

        # --- GALATASARAY (Gidenler - 2026/2027) ---
        {
            "player_name": "Victor Nelsson", "pos": "Stoper", "age": 28, "val": Decimal("5000000"),
            "to_club": ("FC Nordsjaelland", "FCN", "Farum", "Superliga", "https://tmssl.akamaized.net/images/wappen/head/2778.png"),
            "from_team": gs, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 9, 2), "details": "Galatasaray -> FC Nordsjaelland - Bedelsiz", "season_name": "2026/2027"
        },
        {
            "player_name": "Mauro Icardi", "pos": "Santrafor", "age": 33, "val": Decimal("7000000"),
            "to_club": None, "from_team": gs, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 7, 1), "details": "Galatasaray -> Sözleşme Sonu / Serbest", "season_name": "2026/2027"
        },
        {
            "player_name": "Michy Batshuayi", "pos": "Santrafor", "age": 32, "val": Decimal("6000000"),
            "to_club": ("Eintracht Frankfurt", "SGE", "Frankfurt", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/24.png"),
            "from_team": gs, "contract": "PERMANENT", "fee": Decimal("4000000"),
            "date": date(2026, 8, 20), "details": "Galatasaray -> Eintracht Frankfurt - 4.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Hakim Ziyech", "pos": "Sağ Kanat", "age": 33, "val": Decimal("5000000"),
            "to_club": ("Al-Arabi SC", "ARA", "Doha", "Stars League", "https://tmssl.akamaized.net/images/wappen/head/2678.png"),
            "from_team": gs, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 8, 15), "details": "Galatasaray -> Al-Arabi SC - Bedelsiz", "season_name": "2026/2027"
        },
        {
            "player_name": "Ali Turap Bülbül", "pos": "Sağ Bek", "age": 21, "val": Decimal("450000"),
            "from_team": gs, "to_team": amed, "contract": "LOAN", "fee": Decimal("0"),
            "date": date(2026, 8, 20), "details": "Galatasaray -> Amed SK - Kiralık", "season_name": "2026/2027"
        },

        # --- FENERBAHÇE (Gelenler - 2026/2027) ---
        {
            "player_name": "Mason Greenwood", "pos": "Sağ Kanat", "age": 24, "val": Decimal("40000000"),
            "from_club": ("Olympique Marseille", "OM", "Marsilya", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/244.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("39000000"),
            "date": date(2026, 8, 20), "details": "Olympique Marseille -> Fenerbahçe - 39.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Kerem Aktürkoğlu", "pos": "Sol Kanat", "age": 27, "val": Decimal("18000000"),
            "from_club": ("SL Benfica", "BEN", "Lizbon", "Liga Portugal", "https://tmssl.akamaized.net/images/wappen/head/294.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("22500000"),
            "date": date(2026, 8, 28), "details": "SL Benfica -> Fenerbahçe - 22.50M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Dorgeles Nene", "pos": "Santrafor", "age": 23, "val": Decimal("20000000"),
            "from_club": ("Red Bull Salzburg", "RBS", "Salzburg", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/409.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("20000000"),
            "date": date(2026, 8, 22), "details": "Red Bull Salzburg -> Fenerbahçe - 20.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Archie Brown", "pos": "Sol Bek", "age": 24, "val": Decimal("18000000"),
            "from_club": ("KAA Gent", "GNT", "Gent", "Pro League", "https://tmssl.akamaized.net/images/wappen/head/157.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("18000000"),
            "date": date(2026, 8, 25), "details": "KAA Gent -> Fenerbahçe - 18.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Mattéo Guendouzi", "pos": "Merkez Orta Saha", "age": 27, "val": Decimal("27000000"),
            "from_club": ("SS Lazio", "LAZ", "Roma", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/398.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("13000000"),
            "date": date(2026, 7, 20), "details": "SS Lazio -> Fenerbahçe - 13.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Ederson", "pos": "Kaleci", "age": 33, "val": Decimal("8000000"),
            "from_club": ("Manchester City", "MCI", "Manchester", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/281.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("12000000"),
            "date": date(2026, 8, 14), "details": "Manchester City -> Fenerbahçe - 12.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Kojo Oppong", "pos": "Stoper", "age": 22, "val": Decimal("12000000"),
            "from_club": ("FC Nordsjaelland", "FCN", "Farum", "Superliga", "https://tmssl.akamaized.net/images/wappen/head/2778.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("12000000"),
            "date": date(2026, 8, 19), "details": "FC Nordsjaelland -> Fenerbahçe - 12.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Nathan Aké", "pos": "Stoper", "age": 31, "val": Decimal("13000000"),
            "from_club": ("Manchester City", "MCI", "Manchester", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/281.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("10000000"),
            "date": date(2026, 8, 16), "details": "Manchester City -> Fenerbahçe - 10.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Milan Škriniar", "pos": "Stoper", "age": 31, "val": Decimal("12000000"),
            "from_club": ("Paris Saint-Germain", "PSG", "Paris", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/583.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("8000000"),
            "date": date(2026, 8, 12), "details": "Paris Saint-Germain -> Fenerbahçe - 8.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Vedat Muriqi", "pos": "Santrafor", "age": 32, "val": Decimal("8000000"),
            "from_club": ("RCD Mallorca", "MAL", "Palma", "La Liga", "https://tmssl.akamaized.net/images/wappen/head/237.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("8000000"),
            "date": date(2026, 8, 5), "details": "RCD Mallorca -> Fenerbahçe - 8.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "N'Golo Kanté", "pos": "Ön Libero", "age": 35, "val": Decimal("4500000"),
            "from_club": ("Al-Ittihad Club", "ITT", "Cidde", "Saudi Pro League", "https://tmssl.akamaized.net/images/wappen/head/8014.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("4000000"),
            "date": date(2026, 8, 9), "details": "Al-Ittihad -> Fenerbahçe - 4.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Nélson Semedo", "pos": "Sağ Bek", "age": 32, "val": Decimal("5000000"),
            "from_club": ("Wolverhampton Wanderers", "WOL", "Wolverhampton", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/543.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("4000000"),
            "date": date(2026, 8, 7), "details": "Wolverhampton -> Fenerbahçe - 4.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Ognjen Mimović", "pos": "Sağ Bek", "age": 22, "val": Decimal("3500000"),
            "from_club": ("FK Kızılyıldız", "CRV", "Belgrad", "SuperLiga", "https://tmssl.akamaized.net/images/wappen/head/159.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("2500000"),
            "date": date(2026, 8, 23), "details": "FK Kızılyıldız -> Fenerbahçe - 2.50M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Amara Diouf", "pos": "Sol Kanat", "age": 18, "val": Decimal("3000000"),
            "from_club": ("Génération Foot", "GEN", "Dakar", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/35791.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("800000"),
            "date": date(2026, 7, 15), "details": "Génération Foot -> Fenerbahçe - 800k € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Romelu Lukaku", "pos": "Santrafor", "age": 33, "val": Decimal("10000000"),
            "from_club": ("SSC Napoli", "NAP", "Napoli", "Serie A", "https://upload.wikimedia.org/wikipedia/commons/2/28/S.S.C._Napoli_logo.svg"),
            "to_team": fb, "contract": "LOAN", "fee": Decimal("0"),
            "date": date(2026, 8, 25), "details": "SSC Napoli -> Fenerbahçe - Kiralık", "season_name": "2026/2027"
        },
        {
            "player_name": "Marco Asensio", "pos": "On Numara", "age": 30, "val": Decimal("10000000"),
            "from_club": ("Paris Saint-Germain", "PSG", "Paris", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/583.png"),
            "to_team": fb, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 8, 10), "details": "Paris Saint-Germain -> Fenerbahçe - Bedelsiz", "season_name": "2026/2027"
        },
        {
            "player_name": "Mert Günok", "pos": "Kaleci", "age": 37, "val": Decimal("300000"),
            "from_team": bjk, "to_team": fb, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 7, 1), "details": "Beşiktaş -> Fenerbahçe - Bedelsiz", "season_name": "2026/2027"
        },

        # --- FENERBAHÇE (Gidenler - 2026/2027) ---
        {
            "player_name": "Youssef En-Nesyri", "pos": "Santrafor", "age": 29, "val": Decimal("17000000"),
            "to_club": ("Al-Ittihad Club", "ITT", "Cidde", "Saudi Pro League", "https://tmssl.akamaized.net/images/wappen/head/8014.png"),
            "from_team": fb, "contract": "PERMANENT", "fee": Decimal("15000000"),
            "date": date(2026, 8, 12), "details": "Fenerbahçe -> Al-Ittihad Club - 15.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Sebastian Szymański", "pos": "On Numara", "age": 27, "val": Decimal("22000000"),
            "to_club": ("Tottenham Hotspur", "TOT", "Londra", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/148.png"),
            "from_team": fb, "contract": "PERMANENT", "fee": Decimal("22000000"),
            "date": date(2026, 8, 15), "details": "Fenerbahçe -> Tottenham Hotspur - 22.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Dominik Livaković", "pos": "Kaleci", "age": 31, "val": Decimal("12000000"),
            "to_club": ("FC Barcelona", "BAR", "Barselona", "La Liga", "https://tmssl.akamaized.net/images/wappen/head/131.png"),
            "from_team": fb, "contract": "PERMANENT", "fee": Decimal("10000000"),
            "date": date(2026, 8, 8), "details": "Fenerbahçe -> FC Barcelona - 10.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Rodrigo Becão", "pos": "Stoper", "age": 30, "val": Decimal("7000000"),
            "to_club": ("Atalanta BC", "ATA", "Bergamo", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/800.png"),
            "from_team": fb, "contract": "PERMANENT", "fee": Decimal("7000000"),
            "date": date(2026, 8, 12), "details": "Fenerbahçe -> Atalanta BC - 7.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Cengiz Ünder", "pos": "Sağ Kanat", "age": 29, "val": Decimal("8000000"),
            "to_club": ("Los Angeles FC", "LAFC", "Los Angeles", "MLS", "https://tmssl.akamaized.net/images/wappen/head/51828.png"),
            "from_team": fb, "contract": "PERMANENT", "fee": Decimal("8000000"),
            "date": date(2026, 8, 18), "details": "Fenerbahçe -> Los Angeles FC - 8.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Samet Akaydin", "pos": "Stoper", "age": 32, "val": Decimal("1000000"),
            "from_team": fb, "to_team": ts, "contract": "PERMANENT", "fee": Decimal("1000000"),
            "date": date(2026, 8, 20), "details": "Fenerbahçe -> Trabzonspor - 1.00M € Bonservis", "season_name": "2026/2027"
        },

        # --- BEŞİKTAŞ (Gelenler - 2026/2027) ---
        {
            "player_name": "Dušan Vlahović", "pos": "Santrafor", "age": 26, "val": Decimal("32000000"),
            "from_club": ("Juventus FC", "JUV", "Torino", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/506.png"),
            "to_team": bjk, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 8, 1), "details": "Juventus -> Beşiktaş - Bedelsiz", "season_name": "2026/2027"
        },
        {
            "player_name": "Ernest Poku", "pos": "Sağ Kanat", "age": 22, "val": Decimal("22000000"),
            "from_club": ("AZ Alkmaar", "AZA", "Alkmaar", "Eredivisie", "https://tmssl.akamaized.net/images/wappen/head/1090.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("22000000"),
            "date": date(2026, 8, 27), "details": "AZ Alkmaar -> Beşiktaş - 22.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Orkun Kökçü", "pos": "Merkez Orta Saha", "age": 25, "val": Decimal("28000000"),
            "from_club": ("SL Benfica", "BEN", "Lizbon", "Liga Portugal", "https://tmssl.akamaized.net/images/wappen/head/294.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("18000000"),
            "date": date(2026, 8, 11), "details": "SL Benfica -> Beşiktaş - 18.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Fabio Miretti", "pos": "Merkez Orta Saha", "age": 23, "val": Decimal("15000000"),
            "from_club": ("Juventus FC", "JUV", "Torino", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/506.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("15000000"),
            "date": date(2026, 8, 25), "details": "Juventus -> Beşiktaş - 15.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Hyeon-gyu Oh", "pos": "Santrafor", "age": 25, "val": Decimal("15000000"),
            "from_club": ("KRC Genk", "GNK", "Genk", "Pro League", "https://tmssl.akamaized.net/images/wappen/head/1184.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("15000000"),
            "date": date(2026, 8, 21), "details": "KRC Genk -> Beşiktaş - 15.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Leandro Trossard", "pos": "Sol Kanat", "age": 31, "val": Decimal("18000000"),
            "from_club": ("Arsenal FC", "ARS", "Londra", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/11.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("12000000"),
            "date": date(2026, 8, 19), "details": "Arsenal FC -> Beşiktaş - 12.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Emmanuel Agbadou", "pos": "Stoper", "age": 29, "val": Decimal("14000000"),
            "from_club": ("Stade Reims", "SDR", "Reims", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/1421.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("14000000"),
            "date": date(2026, 8, 14), "details": "Stade Reims -> Beşiktaş - 14.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Kassoum Ouattara", "pos": "Sol Bek", "age": 22, "val": Decimal("12000000"),
            "from_club": ("AS Monaco", "ASM", "Monaco", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/162.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("12000000"),
            "date": date(2026, 8, 28), "details": "AS Monaco -> Beşiktaş - 12.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Junior Olaitan", "pos": "On Numara", "age": 24, "val": Decimal("12000000"),
            "from_club": ("ESTAC Troyes", "TRO", "Troyes", "Ligue 2", "https://tmssl.akamaized.net/images/wappen/head/1095.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("12000000"),
            "date": date(2026, 8, 17), "details": "ESTAC Troyes -> Beşiktaş - 12.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Alexander Nübel", "pos": "Kaleci", "age": 29, "val": Decimal("12000000"),
            "from_club": ("Bayern Münih", "FCB", "Münih", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/27.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("8000000"),
            "date": date(2026, 8, 8), "details": "Bayern Münih -> Beşiktaş - 8.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Tiago Djaló", "pos": "Stoper", "age": 26, "val": Decimal("11000000"),
            "from_club": ("Juventus FC", "JUV", "Torino", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/506.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("8000000"),
            "date": date(2026, 8, 18), "details": "Juventus -> Beşiktaş - 8.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Rıdvan Yılmaz", "pos": "Sol Bek", "age": 25, "val": Decimal("7000000"),
            "from_club": ("Rangers FC", "RAN", "Glasgow", "Scottish Premiership", "https://tmssl.akamaized.net/images/wappen/head/124.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("7000000"),
            "date": date(2026, 8, 22), "details": "Rangers FC -> Beşiktaş - 7.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Amir Murillo", "pos": "Sağ Bek", "age": 30, "val": Decimal("7000000"),
            "from_club": ("Olympique Marseille", "OM", "Marsilya", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/244.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("7000000"),
            "date": date(2026, 8, 15), "details": "Olympique Marseille -> Beşiktaş - 7.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "İlhan Fakılı", "pos": "On Numara", "age": 20, "val": Decimal("7000000"),
            "from_club": ("Clermont Foot", "CLE", "Clermont-Ferrand", "Ligue 2", "https://tmssl.akamaized.net/images/wappen/head/3524.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("7000000"),
            "date": date(2026, 8, 12), "details": "Clermont Foot -> Beşiktaş - 7.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Vaclav Cerny", "pos": "Sağ Kanat", "age": 28, "val": Decimal("8000000"),
            "from_club": ("VfL Wolfsburg", "WOB", "Wolfsburg", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/82.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("6000000"),
            "date": date(2026, 7, 30), "details": "VfL Wolfsburg -> Beşiktaş - 6.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Wilfred Ndidi", "pos": "Ön Libero", "age": 29, "val": Decimal("10000000"),
            "from_club": ("Leicester City", "LEI", "Leicester", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/1003.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("6000000"),
            "date": date(2026, 8, 10), "details": "Leicester City -> Beşiktaş - 6.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Taylan Bulut", "pos": "Sağ Bek", "age": 20, "val": Decimal("5000000"),
            "from_club": ("FC Schalke 04", "S04", "Gelsenkirchen", "2. Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/33.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("5000000"),
            "date": date(2026, 8, 5), "details": "Schalke 04 -> Beşiktaş - 5.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Salih Özcan", "pos": "Ön Libero", "age": 28, "val": Decimal("7000000"),
            "from_club": ("Borussia Dortmund", "BVB", "Dortmund", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/16.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("4500000"),
            "date": date(2026, 8, 2), "details": "Borussia Dortmund -> Beşiktaş - 4.50M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Doğan Alemdar", "pos": "Kaleci", "age": 23, "val": Decimal("2500000"),
            "from_club": ("Stade Rennais", "REN", "Rennes", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/273.png"),
            "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("2000000"),
            "date": date(2026, 8, 3), "details": "Stade Rennais -> Beşiktaş - 2.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Ümit Akdağ", "pos": "Stoper", "age": 22, "val": Decimal("8000000"),
            "from_team": alanya, "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("8000000"),
            "date": date(2026, 8, 24), "details": "Alanyaspor -> Beşiktaş - 8.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Yasin Özcan", "pos": "Stoper", "age": 20, "val": Decimal("6000000"),
            "from_team": kasimpasa, "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("5000000"),
            "date": date(2026, 8, 16), "details": "Kasımpaşa -> Beşiktaş - 5.00M € Bonservis", "season_name": "2026/2027"
        },

        # --- BEŞİKTAŞ (Gidenler - 2026/2027) ---
        {
            "player_name": "Ciro Immobile", "pos": "Santrafor", "age": 36, "val": Decimal("3000000"),
            "to_club": ("Bologna FC", "BOL", "Bologna", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/1025.png"),
            "from_team": bjk, "contract": "PERMANENT", "fee": Decimal("2500000"),
            "date": date(2026, 8, 15), "details": "Beşiktaş -> Bologna FC - 2.50M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Arthur Masuaku", "pos": "Sol Bek", "age": 32, "val": Decimal("3000000"),
            "to_club": None, "from_team": bjk, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 8, 18), "details": "Beşiktaş -> Sözleşme Sonu / Serbest", "season_name": "2026/2027"
        },
        {
            "player_name": "Ernest Muci", "pos": "On Numara", "age": 25, "val": Decimal("11000000"),
            "from_team": bjk, "to_team": ts, "contract": "PERMANENT", "fee": Decimal("11000000"),
            "date": date(2026, 8, 27), "details": "Beşiktaş -> Trabzonspor - 11.00M € Bonservis", "season_name": "2026/2027"
        },

        # --- TRABZONSPOR (Gelenler - 2026/2027) ---
        {
            "player_name": "Franculino", "pos": "Santrafor", "age": 22, "val": Decimal("22000000"),
            "from_club": ("FC Midtjylland", "FCM", "Herning", "Superliga", "https://tmssl.akamaized.net/images/wappen/head/1177.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("14000000"),
            "date": date(2026, 8, 24), "details": "FC Midtjylland -> Trabzonspor - 14.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Chibuike Nwaiwu", "pos": "Stoper", "age": 23, "val": Decimal("18000000"),
            "from_club": ("Wolfsberger AC", "WAC", "Wolfsberg", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/4441.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("18000000"),
            "date": date(2026, 8, 20), "details": "Wolfsberger AC -> Trabzonspor - 18.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Mohamed Salah", "pos": "Sağ Kanat", "age": 34, "val": Decimal("17000000"),
            "from_club": ("Liverpool FC", "LIV", "Liverpool", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/31.png"),
            "to_team": ts, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 7, 10), "details": "Liverpool FC -> Trabzonspor - Bedelsiz", "season_name": "2026/2027"
        },
        {
            "player_name": "Aral Şimşir", "pos": "Sol Kanat", "age": 24, "val": Decimal("15000000"),
            "from_club": ("FC Midtjylland", "FCM", "Herning", "Superliga", "https://tmssl.akamaized.net/images/wappen/head/1177.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("15000000"),
            "date": date(2026, 8, 22), "details": "FC Midtjylland -> Trabzonspor - 15.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Wagner Pina", "pos": "Sağ Bek", "age": 23, "val": Decimal("12000000"),
            "from_club": ("GD Estoril Praia", "EST", "Estoril", "Liga Portugal", "https://tmssl.akamaized.net/images/wappen/head/1465.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("12000000"),
            "date": date(2026, 8, 26), "details": "GD Estoril Praia -> Trabzonspor - 12.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Noah Saviolo", "pos": "On Numara", "age": 21, "val": Decimal("12000000"),
            "from_club": ("LOSC Lille", "LIL", "Lille", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/1082.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("12000000"),
            "date": date(2026, 8, 18), "details": "LOSC Lille -> Trabzonspor - 12.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Arseniy Batagov", "pos": "Stoper", "age": 24, "val": Decimal("10000000"),
            "from_club": ("Zorya Lugansk", "ZOR", "Luhansk", "Premier Liga", "https://tmssl.akamaized.net/images/wappen/head/10690.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("10000000"),
            "date": date(2026, 8, 12), "details": "Zorya Lugansk -> Trabzonspor - 10.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Sidny Lopes Cabral", "pos": "Sol Bek", "age": 23, "val": Decimal("10000000"),
            "from_club": ("FC Viktoria Köln", "VIK", "Köln", "3. Liga", "https://tmssl.akamaized.net/images/wappen/head/2856.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("10000000"),
            "date": date(2026, 8, 15), "details": "FC Viktoria Köln -> Trabzonspor - 10.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "André Onana", "pos": "Kaleci", "age": 30, "val": Decimal("20000000"),
            "from_club": ("Manchester United", "MUN", "Manchester", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/985.png"),
            "to_team": ts, "contract": "LOAN", "fee": Decimal("0"),
            "date": date(2026, 8, 29), "details": "Manchester United -> Trabzonspor - Kiralık", "season_name": "2026/2027"
        },
        {
            "player_name": "Fabinho", "pos": "Ön Libero", "age": 32, "val": Decimal("10000000"),
            "from_club": ("Al-Ittihad Club", "ITT", "Cidde", "Saudi Pro League", "https://tmssl.akamaized.net/images/wappen/head/8014.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("8000000"),
            "date": date(2026, 8, 14), "details": "Al-Ittihad -> Trabzonspor - 8.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Tim Jabol-Folcarelli", "pos": "Merkez Orta Saha", "age": 26, "val": Decimal("8000000"),
            "from_club": ("AC Ajaccio", "ACA", "Ajaccio", "Ligue 2", "https://tmssl.akamaized.net/images/wappen/head/1147.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("7000000"),
            "date": date(2026, 8, 16), "details": "AC Ajaccio -> Trabzonspor - 7.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Paul Onuachu", "pos": "Santrafor", "age": 32, "val": Decimal("9000000"),
            "from_club": ("Southampton FC", "SOU", "Southampton", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/180.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("6000000"),
            "date": date(2026, 8, 16), "details": "Southampton -> Trabzonspor - 6.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Benjamin Bouchouari", "pos": "Merkez Orta Saha", "age": 24, "val": Decimal("4000000"),
            "from_club": ("AS Saint-Étienne", "STE", "Saint-Étienne", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/618.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("3500000"),
            "date": date(2026, 8, 11), "details": "AS Saint-Étienne -> Trabzonspor - 3.50M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Cenk Özkaçar", "pos": "Stoper", "age": 25, "val": Decimal("3000000"),
            "from_club": ("Valencia CF", "VAL", "Valencia", "La Liga", "https://tmssl.akamaized.net/images/wappen/head/1049.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("3000000"),
            "date": date(2026, 8, 20), "details": "Valencia CF -> Trabzonspor - 3.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Ruslan Malinovskyi", "pos": "On Numara", "age": 33, "val": Decimal("3000000"),
            "from_club": ("Genoa CFC", "GEN", "Genova", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/252.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("2000000"),
            "date": date(2026, 8, 8), "details": "Genoa CFC -> Trabzonspor - 2.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Mustafa Eskihellaç", "pos": "Sol Bek", "age": 29, "val": Decimal("4000000"),
            "from_team": gaziantep, "to_team": ts, "contract": "PERMANENT", "fee": Decimal("4000000"),
            "date": date(2026, 8, 15), "details": "Gaziantep FK -> Trabzonspor - 4.00M € Bonservis", "season_name": "2026/2027"
        },

        # --- TRABZONSPOR (Gidenler - 2026/2027) ---
        {
            "player_name": "Simon Banza", "pos": "Santrafor", "age": 30, "val": Decimal("16000000"),
            "to_club": ("SC Braga", "BRA", "Braga", "Liga Portugal", "https://tmssl.akamaized.net/images/wappen/head/1075.png"),
            "from_team": ts, "contract": "LOAN", "fee": Decimal("0"),
            "date": date(2026, 6, 30), "details": "Trabzonspor -> SC Braga - Kiralık Dönüşü", "season_name": "2026/2027"
        },
        {
            "player_name": "Enis Bardhi", "pos": "On Numara", "age": 31, "val": Decimal("3000000"),
            "to_club": ("RCD Espanyol", "ESP", "Barselona", "La Liga", "https://tmssl.akamaized.net/images/wappen/head/714.png"),
            "from_team": ts, "contract": "PERMANENT", "fee": Decimal("2500000"),
            "date": date(2026, 8, 14), "details": "Trabzonspor -> RCD Espanyol - 2.50M € Bonservis", "season_name": "2026/2027"
        },

        # --- AMED SK (Gelenler - 2026/2027) ---
        {
            "player_name": "Gift Orban", "pos": "Santrafor", "age": 24, "val": Decimal("10000000"),
            "from_club": ("Olympique Lyon", "OL", "Lyon", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/1041.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("7000000"),
            "date": date(2026, 8, 17), "details": "Olympique Lyon -> Amed SK - 7.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Samuel Ballet", "pos": "Sağ Kanat", "age": 25, "val": Decimal("4000000"),
            "from_club": ("Como 1907", "COM", "Como", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/1047.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("3500000"),
            "date": date(2026, 8, 14), "details": "Como 1907 -> Amed SK - 3.50M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Alban Lafont", "pos": "Kaleci", "age": 27, "val": Decimal("8000000"),
            "from_club": ("FC Nantes", "FCN", "Nantes", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/995.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("3000000"),
            "date": date(2026, 8, 21), "details": "FC Nantes -> Amed SK - 3.00M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Yira Sor", "pos": "Sol Kanat", "age": 26, "val": Decimal("3000000"),
            "from_club": ("KRC Genk", "GNK", "Genk", "Pro League", "https://tmssl.akamaized.net/images/wappen/head/1184.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("2500000"),
            "date": date(2026, 8, 23), "details": "KRC Genk -> Amed SK - 2.50M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Rayan Raveloson", "pos": "Merkez Orta Saha", "age": 29, "val": Decimal("2500000"),
            "from_club": ("AJ Auxerre", "AUX", "Auxerre", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/290.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("1800000"),
            "date": date(2026, 8, 12), "details": "AJ Auxerre -> Amed SK - 1.80M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Amadou Cissé", "pos": "Ön Libero", "age": 23, "val": Decimal("1200000"),
            "from_club": ("Paris FC", "PFC", "Paris", "Ligue 2", "https://tmssl.akamaized.net/images/wappen/head/507.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("800000"),
            "date": date(2026, 8, 8), "details": "Paris FC -> Amed SK - 800k € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Mbaye Diagne", "pos": "Santrafor", "age": 34, "val": Decimal("1000000"),
            "from_club": ("Al-Qadsiah FC", "QAD", "Khobar", "Saudi Pro League", "https://tmssl.akamaized.net/images/wappen/head/8931.png"),
            "to_team": amed, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2026, 8, 5), "details": "Al-Qadsiah -> Amed SK - Bedelsiz", "season_name": "2026/2027"
        },
        {
            "player_name": "Furkan Soyalp", "pos": "Merkez Orta Saha", "age": 31, "val": Decimal("1200000"),
            "from_team": gaziantep, "to_team": amed, "contract": "PERMANENT", "fee": Decimal("1200000"),
            "date": date(2026, 8, 10), "details": "Gaziantep FK -> Amed SK - 1.20M € Bonservis", "season_name": "2026/2027"
        },
        {
            "player_name": "Gökhan Gül", "pos": "Ön Libero", "age": 28, "val": Decimal("1200000"),
            "from_team": kasimpasa, "to_team": amed, "contract": "PERMANENT", "fee": Decimal("1000000"),
            "date": date(2026, 8, 16), "details": "Kasımpaşa -> Amed SK - 1.00M € Bonservis", "season_name": "2026/2027"
        },

        # --- BAŞAKŞEHİR (Gelenler - 2026/2027) ---
        {
            "player_name": "Eldor Shomurodov", "pos": "Santrafor", "age": 31, "val": Decimal("5000000"),
            "from_club": ("AS Roma", "ROM", "Roma", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/12.png"),
            "to_team": ibfk, "contract": "PERMANENT", "fee": Decimal("5000000"),
            "date": date(2026, 8, 10), "details": "AS Roma -> Başakşehir - 5.00M € Bonservis", "season_name": "2026/2027"
        },

        # =========================================================================
        # 2. 2024/2025 GEÇMİŞ SEZON RESMİ TRANSFERLERİ
        # =========================================================================
        # Süper Lig'den Ayrılanlar (2024/2025):
        {
            "player_name": "Tete", "pos": "Sağ Kanat", "age": 25, "val": Decimal("10000000"),
            "to_club": ("Panathinaikos", "PAN", "Atina", "Super League", "https://tmssl.akamaized.net/images/wappen/head/265.png"),
            "from_team": gs, "contract": "PERMANENT", "fee": Decimal("4750000"),
            "date": date(2024, 7, 25), "details": "Galatasaray -> Panathinaikos - 4.75M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Ferdi Kadıoğlu", "pos": "Sol Bek", "age": 25, "val": Decimal("30000000"),
            "to_club": ("Brighton & Hove Albion", "BHA", "Brighton", "Premier League", "https://tmssl.akamaized.net/images/wappen/head/1237.png"),
            "from_team": fb, "contract": "PERMANENT", "fee": Decimal("30000000"),
            "date": date(2024, 8, 23), "details": "Fenerbahçe -> Brighton - 30.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Kerem Aktürkoğlu", "pos": "Sol Kanat", "age": 26, "val": Decimal("18000000"),
            "to_club": ("SL Benfica", "BEN", "Lizbon", "Liga Portugal", "https://tmssl.akamaized.net/images/wappen/head/294.png"),
            "from_team": gs, "contract": "PERMANENT", "fee": Decimal("12000000"),
            "date": date(2024, 9, 3), "details": "Galatasaray -> SL Benfica - 12.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Wilfried Zaha", "pos": "Sol Kanat", "age": 32, "val": Decimal("11000000"),
            "to_club": ("Olympique Lyon", "OL", "Lyon", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/1041.png"),
            "from_team": gs, "contract": "LOAN", "fee": Decimal("3000000"),
            "date": date(2024, 8, 30), "details": "Galatasaray -> Olympique Lyon - 3.00M € Kiralık", "season_name": "2024/2025"
        },
        {
            "player_name": "Derrick Köhn", "pos": "Sol Bek", "age": 26, "val": Decimal("6000000"),
            "to_club": ("SV Werder Bremen", "SVW", "Bremen", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/86.png"),
            "from_team": gs, "contract": "LOAN", "fee": Decimal("0"),
            "date": date(2024, 8, 29), "details": "Galatasaray -> SV Werder Bremen - Kiralık", "season_name": "2024/2025"
        },
        {
            "player_name": "Nicolò Zaniolo", "pos": "Sağ Kanat", "age": 26, "val": Decimal("16000000"),
            "to_club": ("Atalanta BC", "ATA", "Bergamo", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/800.png"),
            "from_team": gs, "contract": "LOAN", "fee": Decimal("6400000"),
            "date": date(2024, 7, 10), "details": "Galatasaray -> Atalanta BC - 6.40M € Kiralık", "season_name": "2024/2025"
        },
        {
            "player_name": "Vincent Aboubakar", "pos": "Santrafor", "age": 33, "val": Decimal("2800000"),
            "to_club": ("Hatayspor", "HAT", "Hatay", "Süper Lig", "https://tmssl.akamaized.net/images/wappen/head/7775.png"),
            "from_team": bjk, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 9, 5), "details": "Beşiktaş -> Hatayspor - Bedelsiz", "season_name": "2024/2025"
        },
        {
            "player_name": "Ante Rebic", "pos": "Sol Kanat", "age": 32, "val": Decimal("1800000"),
            "to_club": ("US Lecce", "LEC", "Lecce", "Serie A", "https://tmssl.akamaized.net/images/wappen/head/1005.png"),
            "from_team": bjk, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 8, 26), "details": "Beşiktaş -> US Lecce - Bedelsiz", "season_name": "2024/2025"
        },
        {
            "player_name": "Jackson Muleka", "pos": "Santrafor", "age": 26, "val": Decimal("3500000"),
            "to_club": ("Al-Kholood Club", "KHO", "Rass", "Saudi Pro League", "https://tmssl.akamaized.net/images/wappen/head/82331.png"),
            "from_team": bjk, "contract": "LOAN", "fee": Decimal("1000000"),
            "date": date(2024, 8, 22), "details": "Beşiktaş -> Al-Kholood - 1.00M € Kiralık", "season_name": "2024/2025"
        },
        {
            "player_name": "Daniel Amartey", "pos": "Stoper", "age": 31, "val": Decimal("2000000"),
            "to_club": None, "from_team": bjk, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 8, 15), "details": "Beşiktaş -> Serbest - Sözleşme Feshi", "season_name": "2024/2025"
        },
        {
            "player_name": "Thomas Meunier", "pos": "Sağ Bek", "age": 34, "val": Decimal("2500000"),
            "to_club": ("LOSC Lille", "LIL", "Lille", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/1082.png"),
            "from_team": ts, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 7, 19), "details": "Trabzonspor -> LOSC Lille - Bedelsiz", "season_name": "2024/2025"
        },
        {
            "player_name": "Nicolas Pépé", "pos": "Sağ Kanat", "age": 30, "val": Decimal("8000000"),
            "to_club": ("Villarreal CF", "VIL", "Villarreal", "La Liga", "https://tmssl.akamaized.net/images/wappen/head/1050.png"),
            "from_team": ts, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 8, 4), "details": "Trabzonspor -> Villarreal CF - Bedelsiz", "season_name": "2024/2025"
        },
        {
            "player_name": "Trezeguet", "pos": "Sol Kanat", "age": 31, "val": Decimal("6500000"),
            "to_club": ("Al-Rayyan SC", "RAY", "Er-Reyyan", "Stars League", "https://tmssl.akamaized.net/images/wappen/head/10260.png"),
            "from_team": ts, "contract": "LOAN", "fee": Decimal("0"),
            "date": date(2024, 9, 3), "details": "Trabzonspor -> Al-Rayyan - Kiralık", "season_name": "2024/2025"
        },
        {
            "player_name": "Rade Krunic", "pos": "Ön Libero", "age": 32, "val": Decimal("3500000"),
            "to_club": ("FK Kızılyıldız", "CRV", "Belgrad", "SuperLiga", "https://tmssl.akamaized.net/images/wappen/head/159.png"),
            "from_team": fb, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 9, 3), "details": "Fenerbahçe -> FK Kızılyıldız - Bedelsiz", "season_name": "2024/2025"
        },
        {
            "player_name": "Miha Zajc", "pos": "Merkez Orta Saha", "age": 31, "val": Decimal("2000000"),
            "to_club": ("Toulouse FC", "TFC", "Toulouse", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/415.png"),
            "from_team": fb, "contract": "LOAN", "fee": Decimal("0"),
            "date": date(2024, 8, 27), "details": "Fenerbahçe -> Toulouse FC - Kiralık", "season_name": "2024/2025"
        },
        {
            "player_name": "Luan Peres", "pos": "Stoper", "age": 31, "val": Decimal("1500000"),
            "to_club": ("Santos FC", "SAN", "Santos", "Série B", "https://tmssl.akamaized.net/images/wappen/head/221.png"),
            "from_team": fb, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 9, 3), "details": "Fenerbahçe -> Santos FC - Bedelsiz", "season_name": "2024/2025"
        },
        {
            "player_name": "Ryan Kent", "pos": "Sol Kanat", "age": 29, "val": Decimal("2000000"),
            "to_club": None, "from_team": fb, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 10, 17), "details": "Fenerbahçe -> Serbest - Sözleşme Feshi", "season_name": "2024/2025"
        },
        {
            "player_name": "João Pedro", "pos": "Santrafor", "age": 33, "val": Decimal("1500000"),
            "to_club": ("Hull City", "HUL", "Kingston upon Hull", "Championship", "https://tmssl.akamaized.net/images/wappen/head/3008.png"),
            "from_team": fb, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 8, 1), "details": "Fenerbahçe -> Hull City - Bedelsiz", "season_name": "2024/2025"
        },

        # Süper Lig'e Gelenler (2024/2025 Geçmiş Sezon):
        {
            "player_name": "Gabriel Sara", "pos": "Merkez Orta Saha", "age": 27, "val": Decimal("27000000"),
            "from_club": ("Norwich City", "NOR", "Norwich", "Championship", "https://tmssl.akamaized.net/images/wappen/head/1123.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("18000000"),
            "date": date(2024, 8, 4), "details": "Norwich City -> Galatasaray - 18.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Ismail Jakobs", "pos": "Sol Bek", "age": 27, "val": Decimal("8000000"),
            "from_club": ("AS Monaco", "ASM", "Monaco", "Ligue 1", "https://tmssl.akamaized.net/images/wappen/head/162.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("8000000"),
            "date": date(2024, 9, 1), "details": "AS Monaco -> Galatasaray - 8.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Roland Sallai", "pos": "Sağ Bek", "age": 29, "val": Decimal("12000000"),
            "from_club": ("SC Freiburg", "SCF", "Freiburg", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/60.png"),
            "to_team": gs, "contract": "PERMANENT", "fee": Decimal("6000000"),
            "date": date(2024, 9, 3), "details": "SC Freiburg -> Galatasaray - 6.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Youssef En-Nesyri", "pos": "Santrafor", "age": 29, "val": Decimal("20000000"),
            "from_club": ("Sevilla FC", "SEV", "Sevilla", "La Liga", "https://tmssl.akamaized.net/images/wappen/head/368.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("19500000"),
            "date": date(2024, 7, 28), "details": "Sevilla FC -> Fenerbahçe - 19.50M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Oğuz Aydın", "pos": "Sol Kanat", "age": 25, "val": Decimal("6000000"),
            "from_team": alanya, "to_team": fb, "contract": "PERMANENT", "fee": Decimal("6000000"),
            "date": date(2024, 7, 15), "details": "Alanyaspor -> Fenerbahçe - 6.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Levent Mercan", "pos": "Sol Bek", "age": 25, "val": Decimal("3000000"),
            "from_club": ("Fatih Karagümrük", "FKG", "İstanbul", "1. Lig", "https://tmssl.akamaized.net/images/wappen/head/5239.png"),
            "to_team": fb, "contract": "PERMANENT", "fee": Decimal("2000000"),
            "date": date(2024, 7, 12), "details": "Fatih Karagümrük -> Fenerbahçe - 2.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Rafa Silva", "pos": "On Numara", "age": 33, "val": Decimal("8000000"),
            "from_club": ("SL Benfica", "BEN", "Lizbon", "Liga Portugal", "https://tmssl.akamaized.net/images/wappen/head/294.png"),
            "to_team": bjk, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 7, 1), "details": "SL Benfica -> Beşiktaş - Bedelsiz", "season_name": "2024/2025"
        },
        {
            "player_name": "Emirhan Topçu", "pos": "Stoper", "age": 26, "val": Decimal("5000000"),
            "from_team": rize, "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("3400000"),
            "date": date(2024, 8, 2), "details": "Çaykur Rizespor -> Beşiktaş - 3.40M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Can Keleş", "pos": "Sağ Kanat", "age": 25, "val": Decimal("3000000"),
            "from_team": kocaeli, "to_team": bjk, "contract": "PERMANENT", "fee": Decimal("2750000"),
            "date": date(2024, 7, 22), "details": "Kocaelispor -> Beşiktaş - 2.75M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Stefan Savić", "pos": "Stoper", "age": 35, "val": Decimal("2000000"),
            "from_club": ("Atlético de Madrid", "ATM", "Madrid", "La Liga", "https://tmssl.akamaized.net/images/wappen/head/13.png"),
            "to_team": ts, "contract": "FREE", "fee": Decimal("0"),
            "date": date(2024, 7, 26), "details": "Atlético de Madrid -> Trabzonspor - Bedelsiz", "season_name": "2024/2025"
        },
        {
            "player_name": "Okay Yokuşlu", "pos": "Ön Libero", "age": 32, "val": Decimal("2500000"),
            "from_club": ("West Bromwich Albion", "WBA", "West Bromwich", "Championship", "https://tmssl.akamaized.net/images/wappen/head/984.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("1650000"),
            "date": date(2024, 7, 31), "details": "West Brom -> Trabzonspor - 1.65M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Ozan Tufan", "pos": "Merkez Orta Saha", "age": 31, "val": Decimal("2500000"),
            "from_club": ("Hull City", "HUL", "Kingston upon Hull", "Championship", "https://tmssl.akamaized.net/images/wappen/head/3008.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("2000000"),
            "date": date(2024, 7, 24), "details": "Hull City -> Trabzonspor - 2.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Cihan Çanak", "pos": "Sağ Kanat", "age": 21, "val": Decimal("4000000"),
            "from_club": ("Standard Liège", "STA", "Liège", "Pro League", "https://tmssl.akamaized.net/images/wappen/head/3057.png"),
            "to_team": ts, "contract": "PERMANENT", "fee": Decimal("1800000"),
            "date": date(2024, 7, 28), "details": "Standard Liège -> Trabzonspor - 1.80M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Lumbardh Dellova", "pos": "Stoper", "age": 27, "val": Decimal("2000000"),
            "from_club": ("CSKA Sofia", "CSK", "Sofya", "efbet Liga", "https://tmssl.akamaized.net/images/wappen/head/28.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("2000000"),
            "date": date(2024, 7, 18), "details": "CSKA Sofia -> Amed SK - 2.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "David Bates", "pos": "Stoper", "age": 29, "val": Decimal("1500000"),
            "from_club": ("Standard Liège", "STA", "Liège", "Pro League", "https://tmssl.akamaized.net/images/wappen/head/3057.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("1500000"),
            "date": date(2024, 7, 24), "details": "Standard Liège -> Amed SK - 1.50M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Dia Saba", "pos": "On Numara", "age": 33, "val": Decimal("2000000"),
            "from_club": ("Maccabi Haifa", "MAC", "Hayfa", "Ligat ha'Al", "https://tmssl.akamaized.net/images/wappen/head/322.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("2000000"),
            "date": date(2024, 7, 29), "details": "Maccabi Haifa -> Amed SK - 2.00M € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Mehmet Yeşil", "pos": "Stoper", "age": 28, "val": Decimal("900000"),
            "from_club": ("İstanbulspor", "İST", "İstanbul", "1. Lig", "https://tmssl.akamaized.net/images/wappen/head/924.png"),
            "to_team": amed, "contract": "PERMANENT", "fee": Decimal("900000"),
            "date": date(2024, 7, 26), "details": "İstanbulspor -> Amed SK - 900k € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Umut Meraş", "pos": "Sol Bek", "age": 30, "val": Decimal("750000"),
            "from_team": bjk, "to_team": amed, "contract": "PERMANENT", "fee": Decimal("750000"),
            "date": date(2024, 8, 14), "details": "Beşiktaş -> Amed SK - 750k € Bonservis", "season_name": "2024/2025"
        },
        {
            "player_name": "Sinan Kurt", "pos": "Merkez Orta Saha", "age": 31, "val": Decimal("600000"),
            "from_team": eyup, "to_team": amed, "contract": "PERMANENT", "fee": Decimal("600000"),
            "date": date(2024, 8, 28), "details": "Eyüpspor -> Amed SK - 600k € Bonservis", "season_name": "2024/2025"
        },

        # =========================================================================
        # 3. 2023/2024 GEÇMİŞ SEZON RESMİ TRANSFERLERİ
        # =========================================================================
        {
            "player_name": "Sacha Boey", "pos": "Sağ Bek", "age": 24, "val": Decimal("28000000"),
            "to_club": ("Bayern Münih", "FCB", "Münih", "Bundesliga", "https://tmssl.akamaized.net/images/wappen/head/27.png"),
            "from_team": gs, "contract": "PERMANENT", "fee": Decimal("30000000"),
            "date": date(2024, 1, 28), "details": "Galatasaray -> Bayern Münih - 30.00M € Bonservis", "season_name": "2023/2024"
        },
    ]
