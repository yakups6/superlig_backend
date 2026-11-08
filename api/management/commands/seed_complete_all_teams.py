# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from api.models import Team, Player, Season, PlayerSeasonStats
from decimal import Decimal

class Command(BaseCommand):
    help = "Seed complete 2026/2027 squads for all remaining 13 Süper Lig clubs"

    def handle(self, *args, **options):
        active_season = Season.get_active_season()
        if not active_season:
            self.stdout.write(self.style.ERROR("Aktif sezon bulunamadı."))
            return

        team_squads = {
            10: { # Başakşehir
                "players": [
                    ("Krzysztof Piątek", "Santrafor", 9, 12000000, "Polonya", 29),
                    ("João Figueiredo", "Santrafor", 11, 4000000, "Brezilya", 28),
                    ("Deniz Türüç", "Sağ Kanat", 23, 2500000, "Türkiye", 31),
                    ("Serdar Gürler", "Sol Kanat", 7, 1500000, "Türkiye", 33),
                    ("Philippe Keny", "Santrafor", 17, 2200000, "Senegal", 25),
                    ("Davidson", "Sol Kanat", 91, 1500000, "Brezilya", 33),
                    ("Olivier Kemen", "Merkez Orta Saha", 8, 3500000, "Kamerun", 28),
                    ("Berat Özdemir", "Ön Libero", 5, 4000000, "Türkiye", 26),
                    ("Miguel Crespo", "Merkez Orta Saha", 27, 4000000, "Portekiz", 28),
                    ("Onur Ergün", "Ön Libero", 4, 800000, "Türkiye", 31),
                    ("Berkay Özcan", "On Numara", 10, 3000000, "Türkiye", 26),
                    ("Jerome Opoku", "Stoper", 3, 4500000, "Gana", 26),
                    ("Léo Duarte", "Stoper", 2, 3500000, "Brezilya", 28),
                    ("Ousseynou Ba", "Stoper", 15, 3000000, "Senegal", 28),
                    ("Hamza Güreler", "Stoper", 25, 1000000, "Türkiye", 18),
                    ("Lucas Lima", "Sol Bek", 6, 1800000, "Brezilya", 33),
                    ("Ömer Ali Şahiner", "Sağ Bek", 42, 1000000, "Türkiye", 32),
                    ("Leo Dubois", "Sağ Bek", 20, 2500000, "Fransa", 30),
                    ("Muhammed Şengezer", "Kaleci", 16, 2000000, "Türkiye", 27),
                    ("Volkan Babacan", "Kaleci", 1, 200000, "Türkiye", 36),
                ]
            },
            17: { # Samsunspor
                "players": [
                    ("Olivier Ntcham", "Merkez Orta Saha", 10, 4500000, "Kamerun", 28),
                    ("Carlo Holse", "On Numara", 21, 4500000, "Danimarka", 25),
                    ("Marius Mouandilmadji", "Santrafor", 9, 3500000, "Çad", 26),
                    ("Arbnor Muja", "Sol Kanat", 7, 3000000, "Arnavutluk", 25),
                    ("Landry Dimata", "Santrafor", 14, 2000000, "Belçika", 27),
                    ("Kingsley Schindler", "Sağ Kanat", 11, 1500000, "Gana", 31),
                    ("Emre Kılınç", "Sol Kanat", 17, 2500000, "Türkiye", 30),
                    ("Flavien Tait", "Merkez Orta Saha", 8, 1500000, "Fransa", 31),
                    ("Celil Yüksel", "Ön Libero", 6, 900000, "Türkiye", 26),
                    ("Soner Aydoğdu", "Merkez Orta Saha", 5, 700000, "Türkiye", 33),
                    ("Rick van Drongelen", "Stoper", 4, 3000000, "Hollanda", 25),
                    ("Lubomir Satka", "Stoper", 37, 2500000, "Slovakya", 28),
                    ("Yunus Emre Çift", "Stoper", 22, 1000000, "Türkiye", 21),
                    ("Marc Bola", "Sol Bek", 18, 1800000, "İngiltere", 26),
                    ("Zeki Yavru", "Sağ Bek", 72, 500000, "Türkiye", 33),
                    ("Soner Gönül", "Sol Bek", 28, 600000, "Türkiye", 27),
                    ("Okan Kocuk", "Kaleci", 1, 2500000, "Türkiye", 29),
                    ("Haluk Mustafa Tan", "Kaleci", 12, 300000, "Türkiye", 19),
                    ("Ercan Kara", "Santrafor", 29, 1500000, "Avusturya", 28),
                    ("Gaëtan Laura", "Santrafor", 99, 1000000, "Fransa", 29),
                ]
            },
            13: { # Göztepe
                "players": [
                    ("Romulo Cardoso", "Santrafor", 79, 5000000, "Brezilya", 22),
                    ("David Tijanic", "On Numara", 43, 2500000, "Slovenya", 27),
                    ("Anthony Dennis", "Ön Libero", 5, 3500000, "Nijerya", 20),
                    ("Isaac Solet", "Merkez Orta Saha", 24, 2000000, "Orta Afrika Cum.", 23),
                    ("Kuryu Matsuki", "On Numara", 17, 3000000, "Japonya", 21),
                    ("Juan Santos", "Santrafor", 9, 3000000, "Brezilya", 22),
                    ("Kubilay Kanatsızkuş", "Santrafor", 19, 1000000, "Türkiye", 27),
                    ("Ahmed Ildız", "Merkez Orta Saha", 8, 900000, "Türkiye", 27),
                    ("Doğan Erdoğan", "Ön Libero", 6, 800000, "Türkiye", 28),
                    ("Malcom Bokele", "Stoper", 4, 2500000, "Kamerun", 24),
                    ("Héliton", "Stoper", 33, 2000000, "Brezilya", 28),
                    ("Taha Altıkardeş", "Stoper", 12, 2500000, "Türkiye", 21),
                    ("Koray Günter", "Stoper", 22, 1500000, "Almanya", 30),
                    ("Djalma Silva", "Sol Bek", 66, 1500000, "Brezilya", 29),
                    ("İsmail Köybaşı", "Sol Bek", 3, 400000, "Türkiye", 35),
                    ("Ogün Bayrak", "Sağ Bek", 77, 1200000, "Türkiye", 26),
                    ("Nazım Sangaré", "Sağ Bek", 30, 600000, "Türkiye", 30),
                    ("Mateusz Lis", "Kaleci", 1, 2500000, "Polonya", 27),
                    ("Arda Özçimen", "Kaleci", 97, 800000, "Türkiye", 22),
                    ("David Datro Fofana", "Santrafor", 99, 4500000, "Fildişi Sahili", 21),
                ]
            },
            7: { # Kasımpaşa
                "players": [
                    ("Haris Hajradinović", "On Numara", 10, 4500000, "Bosna-Hersek", 30),
                    ("Nuno Da Costa", "Santrafor", 9, 2500000, "Yeşil Burun Adaları", 33),
                    ("Mamadou Fall", "Sağ Kanat", 7, 2500000, "Senegal", 32),
                    ("Mortadha Ben Ouanes", "Sol Kanat", 12, 2000000, "Tunus", 30),
                    ("Aytaç Kara", "Merkez Orta Saha", 35, 2000000, "Türkiye", 31),
                    ("Gökhan Gül", "Ön Libero", 6, 2000000, "Almanya", 26),
                    ("Cafú", "Ön Libero", 5, 1500000, "Portekiz", 31),
                    ("Loret Sadiku", "Ön Libero", 8, 600000, "Kosova", 33),
                    ("Claudio Winck", "Sağ Bek", 2, 2000000, "Brezilya", 30),
                    ("Nicholas Opoku", "Stoper", 4, 2000000, "Gana", 27),
                    ("Sadık Çiftpınar", "Stoper", 3, 500000, "Türkiye", 31),
                    ("Yasin Özcan", "Stoper", 58, 4500000, "Türkiye", 18),
                    ("Kévin Rodrigues", "Sol Bek", 20, 1200000, "Portekiz", 30),
                    ("Jhon Espinoza", "Sağ Bek", 77, 1500000, "Ekvador", 25),
                    ("Andreas Gianniotis", "Kaleci", 1, 1500000, "Yunanistan", 31),
                    ("Ali Emre Yanar", "Kaleci", 25, 400000, "Türkiye", 26),
                    ("Erdem Çetinkaya", "Santrafor", 14, 500000, "Türkiye", 23),
                    ("Sinan Malkoç", "Merkez Orta Saha", 18, 500000, "Türkiye", 21),
                ]
            },
            18: { # Eyüpspor
                "players": [
                    ("Mame Thiam", "Santrafor", 9, 3500000, "Senegal", 32),
                    ("Ahmed Kutucu", "Sol Kanat", 7, 4000000, "Türkiye", 24),
                    ("Emre Akbaba", "On Numara", 10, 2500000, "Türkiye", 31),
                    ("Samu Sáiz", "On Numara", 11, 2500000, "İspanya", 33),
                    ("Prince Ampem", "Sağ Kanat", 28, 2500000, "Gana", 26),
                    ("Halil Akbunar", "Sağ Kanat", 77, 1500000, "Türkiye", 30),
                    ("Gianni Bruno", "Santrafor", 19, 800000, "Belçika", 33),
                    ("Fredrik Midtsjø", "Merkez Orta Saha", 18, 2000000, "Norveç", 31),
                    ("Melih Kabasakal", "Ön Libero", 6, 1500000, "Türkiye", 28),
                    ("Robin Yalçın", "Ön Libero", 5, 1000000, "Türkiye", 30),
                    ("Taşkın İlter", "Merkez Orta Saha", 8, 600000, "Azerbaycan", 30),
                    ("Rúben Vezo", "Stoper", 4, 2000000, "Portekiz", 30),
                    ("Luccas Claro", "Stoper", 3, 1500000, "Brezilya", 33),
                    ("Caner Erkin", "Sol Bek", 88, 400000, "Türkiye", 36),
                    ("Umut Meraş", "Sol Bek", 70, 800000, "Türkiye", 28),
                    ("Tayfur Bingöl", "Sağ Bek", 17, 1200000, "Türkiye", 31),
                    ("Berke Özer", "Kaleci", 1, 3500000, "Türkiye", 24),
                    ("Alp Köseer", "Kaleci", 71, 300000, "Türkiye", 21),
                ]
            },
            12: { # Çaykur Rizespor
                "players": [
                    ("Dal Varesanovic", "On Numara", 8, 4500000, "Bosna-Hersek", 23),
                    ("Ibrahim Olawoyin", "Merkez Orta Saha", 10, 3500000, "Nijerya", 26),
                    ("Ali Sowe", "Santrafor", 9, 3000000, "Gambiya", 30),
                    ("Martin Minchev", "Santrafor", 11, 2500000, "Bulgaristan", 23),
                    ("David Akintola", "Sağ Kanat", 7, 2000000, "Nijerya", 28),
                    ("Altin Zeqiri", "Sol Kanat", 77, 2000000, "Kosova", 24),
                    ("Amir Hadziahmetovic", "Ön Libero", 6, 4000000, "Bosna-Hersek", 27),
                    ("Giannis Papanikolaou", "Ön Libero", 5, 2500000, "Yunanistan", 25),
                    ("Mithat Pala", "Merkez Orta Saha", 54, 1200000, "Türkiye", 24),
                    ("Muhammet Taha Şahin", "Sağ Bek", 37, 1800000, "Türkiye", 23),
                    ("Husniddin Alikulov", "Stoper", 2, 2500000, "Özbekistan", 25),
                    ("Attila Mocsi", "Stoper", 4, 2500000, "Macaristan", 24),
                    ("Casper Højer", "Sol Bek", 3, 2000000, "Danimarka", 29),
                    ("Halil İbrahim Pehlivan", "Sol Bek", 53, 500000, "Türkiye", 31),
                    ("Ivo Grbić", "Kaleci", 1, 2500000, "Hırvatistan", 28),
                    ("Tarık Çetin", "Kaleci", 23, 800000, "Türkiye", 27),
                    ("Emrecan Bulut", "Sol Kanat", 28, 1000000, "Türkiye", 21),
                ]
            },
            9: { # Corendon Alanyaspor
                "players": [
                    ("Sergio Córdova", "Santrafor", 9, 2500000, "Venezuela", 27),
                    ("Efecan Karaca", "Sağ Kanat", 7, 1200000, "Türkiye", 34),
                    ("Nicolas Janvier", "Merkez Orta Saha", 10, 2200000, "Fransa", 26),
                    ("Richard", "Ön Libero", 25, 2500000, "Brezilya", 30),
                    ("Gaius Makouta", "Merkez Orta Saha", 8, 2000000, "Kongo", 27),
                    ("Loide Augusto", "Sol Kanat", 11, 2500000, "Angola", 24),
                    ("Hwang Ui-jo", "Santrafor", 16, 2000000, "Güney Kore", 32),
                    ("Florent Hadergjonaj", "Sağ Bek", 42, 2000000, "Kosova", 30),
                    ("Fidan Aliti", "Stoper", 5, 1800000, "Kosova", 30),
                    ("Furkan Bayır", "Stoper", 4, 2000000, "Türkiye", 23),
                    ("Nuno Lima", "Stoper", 3, 1500000, "Portekiz", 23),
                    ("Jure Balkovec", "Sol Bek", 29, 1500000, "Slovenya", 30),
                    ("Fatih Aksoy", "Stoper", 20, 1000000, "Türkiye", 26),
                    ("Ertuğrul Taşkıran", "Kaleci", 1, 600000, "Türkiye", 34),
                    ("Mert Furkan Bayram", "Kaleci", 23, 500000, "Türkiye", 19),
                    ("Anderson Silva", "Santrafor", 17, 1200000, "Brezilya", 26),
                ]
            },
            14: { # Gaziantep FK
                "players": [
                    ("Alexandru Maxim", "On Numara", 44, 2000000, "Romanya", 34),
                    ("David Okereke", "Santrafor", 9, 3500000, "Nijerya", 27),
                    ("Deian Sorescu", "Sağ Kanat", 22, 2200000, "Romanya", 27),
                    ("Halil Dervişoğlu", "Santrafor", 11, 2000000, "Türkiye", 24),
                    ("Kacper Kozłowski", "Merkez Orta Saha", 10, 3500000, "Polonya", 20),
                    ("Badou Ndiaye", "Ön Libero", 18, 1000000, "Senegal", 33),
                    ("Ogün Özçiçek", "Ön Libero", 5, 1500000, "Türkiye", 25),
                    ("Christopher Lungoyi", "Sol Kanat", 7, 1500000, "İsviçre", 24),
                    ("Mustafa Eskihellaç", "Sağ Bek", 17, 2200000, "Türkiye", 27),
                    ("Arda Kızıldağ", "Stoper", 4, 2000000, "Türkiye", 25),
                    ("Bruno Viana", "Stoper", 3, 2500000, "Brezilya", 29),
                    ("Enric Saborit", "Stoper", 13, 1000000, "İspanya", 32),
                    ("Ertuğrul Ersoy", "Stoper", 15, 1200000, "Türkiye", 27),
                    ("Diogo Sousa", "Kaleci", 1, 1800000, "Portekiz", 26),
                    ("Mustafa Burak Bozan", "Kaleci", 71, 400000, "Türkiye", 24),
                    ("Kenan Kodro", "Santrafor", 19, 1000000, "Bosna-Hersek", 31),
                ]
            },
            16: { # Tümosan Konyaspor
                "players": [
                    ("Pedrinho", "On Numara", 10, 2500000, "Brezilya", 31),
                    ("Danijel Aleksic", "On Numara", 91, 1500000, "Sırbistan", 33),
                    ("Umut Nayir", "Santrafor", 22, 2000000, "Türkiye", 31),
                    ("Blaz Kramer", "Santrafor", 9, 2000000, "Slovenya", 28),
                    ("Alassane Ndao", "Sağ Kanat", 18, 2000000, "Senegal", 27),
                    ("Melih İbrahimoğlu", "Merkez Orta Saha", 8, 1500000, "Türkiye", 24),
                    ("Marko Jevtovic", "Ön Libero", 16, 1200000, "Sırbistan", 31),
                    ("Emmanuel Boateng", "Ön Libero", 6, 1500000, "Gana", 27),
                    ("Riechedly Bazoer", "Stoper", 5, 2500000, "Hollanda", 27),
                    ("Adil Demirbağ", "Stoper", 4, 2000000, "Türkiye", 26),
                    ("Uğurcan Yazğılı", "Stoper", 15, 1200000, "Türkiye", 25),
                    ("Guilherme Sityá", "Sol Bek", 12, 1500000, "Brezilya", 34),
                    ("Nikola Boranijasevic", "Sağ Bek", 2, 1200000, "Sırbistan", 32),
                    ("Jakub Slowik", "Kaleci", 1, 800000, "Polonya", 33),
                    ("Deniz Ertaş", "Kaleci", 96, 1200000, "Türkiye", 19),
                    ("Hamidou Keyta", "Sol Kanat", 7, 1000000, "Fransa", 30),
                ]
            },
            8: { # Kocaelispor
                "players": [
                    ("Ryan Mendes", "Sol Kanat", 20, 1500000, "Yeşil Burun Adaları", 34),
                    ("Marcão", "Santrafor", 9, 2000000, "Brezilya", 30),
                    ("Giorgi Beridze", "Sağ Kanat", 11, 1500000, "Gürcistan", 27),
                    ("Mijo Caktas", "On Numara", 10, 1500000, "Hırvatistan", 32),
                    ("Josip Vukovic", "Ön Libero", 6, 1200000, "Hırvatistan", 32),
                    ("Pedrinho", "Merkez Orta Saha", 8, 1000000, "Portekiz", 31),
                    ("Cihat Çelik", "Merkez Orta Saha", 17, 700000, "Türkiye", 28),
                    ("Barış Alıcı", "Sağ Kanat", 7, 700000, "Türkiye", 27),
                    ("Aaron Appindangoyé", "Stoper", 4, 1000000, "Gabon", 32),
                    ("Tarkan Serbest", "Stoper", 5, 800000, "Türkiye", 30),
                    ("Muharrem Cinan", "Sol Bek", 3, 600000, "Türkiye", 26),
                    ("Ahmet Oğuz", "Sağ Bek", 22, 800000, "Türkiye", 31),
                    ("Gökhan Değirmenci", "Kaleci", 1, 300000, "Türkiye", 35),
                    ("Harun Tekin", "Kaleci", 35, 400000, "Türkiye", 35),
                    ("Christian Kouakou", "Santrafor", 14, 500000, "İsveç", 33),
                    ("Onur Atasayar", "Sol Bek", 19, 400000, "Türkiye", 29),
                ]
            },
            15: { # Gençlerbirliği
                "players": [
                    ("Mustapha Yatabaré", "Santrafor", 9, 500000, "Mali", 38),
                    ("Amilton", "Sağ Kanat", 11, 800000, "Brezilya", 35),
                    ("Tiago Çukur", "Santrafor", 19, 800000, "Türkiye", 21),
                    ("Jimmy Durmaz", "On Numara", 10, 400000, "İsveç", 35),
                    ("Rahman Buğra Çağıran", "Ön Libero", 6, 600000, "Türkiye", 29),
                    ("Ensar Kemaloğlu", "Merkez Orta Saha", 8, 700000, "Türkiye", 25),
                    ("Musa Çağıran", "Ön Libero", 5, 400000, "Türkiye", 31),
                    ("Mete Kaan Demir", "Sol Kanat", 7, 700000, "Türkiye", 26),
                    ("Alperen Babacan", "Stoper", 4, 700000, "Türkiye", 27),
                    ("Sinan Osmanoğlu", "Stoper", 15, 500000, "Türkiye", 34),
                    ("Yasin Güreler", "Sol Bek", 3, 400000, "Türkiye", 33),
                    ("Fıratcan Üzüm", "Sağ Bek", 22, 500000, "Türkiye", 25),
                    ("Orkun Özdemir", "Kaleci", 1, 500000, "Türkiye", 29),
                    ("Erhan Erentürk", "Kaleci", 13, 400000, "Türkiye", 29),
                    ("Elias Durmaz", "Sol Kanat", 70, 400000, "İsveç", 24),
                    ("Melih Bostan", "Santrafor", 23, 600000, "Türkiye", 20),
                ]
            },
            11: { # Erzurumspor FK
                "players": [
                    ("Eren Tozlu", "Santrafor", 9, 600000, "Türkiye", 34),
                    ("Mustafa Fettahoğlu", "Sağ Kanat", 11, 400000, "Türkiye", 24),
                    ("Süleyman Koç", "Sağ Kanat", 7, 300000, "Türkiye", 35),
                    ("Martin Hasek", "Merkez Orta Saha", 10, 700000, "Çek Cumhuriyeti", 29),
                    ("Sefa Akgün", "Merkez Orta Saha", 8, 600000, "Türkiye", 24),
                    ("Özgür Sert", "Ön Libero", 6, 500000, "Türkiye", 23),
                    ("Batuhan Artarslan", "Ön Libero", 5, 400000, "Türkiye", 30),
                    ("Mustafa Yumlu", "Stoper", 22, 400000, "Türkiye", 37),
                    ("Yakup Kırtay", "Stoper", 4, 600000, "Türkiye", 21),
                    ("Orhan Ovacıklı", "Sağ Bek", 2, 300000, "Türkiye", 35),
                    ("Celal Hanalp", "Sol Bek", 3, 500000, "Türkiye", 24),
                    ("Mehmet Göktuğ Bakırbaş", "Kaleci", 1, 700000, "Türkiye", 28),
                    ("Rıdvan Oğuzhan Yağcı", "Kaleci", 13, 200000, "Türkiye", 23),
                    ("Cengizhan Bayrak", "Sol Bek", 77, 300000, "Türkiye", 24),
                    ("Alperen Karaca", "Santrafor", 19, 200000, "Türkiye", 20),
                    ("Muhammed Emin Yavaş", "Merkez Orta Saha", 20, 200000, "Türkiye", 20),
                ]
            },
            6: { # Arca Çorum FK
                "players": [
                    ("Thomas Verheydt", "Santrafor", 9, 700000, "Hollanda", 32),
                    ("Kabongo Kasongo", "Santrafor", 99, 800000, "Kongo DC", 30),
                    ("Geraldo", "Sağ Kanat", 11, 600000, "Angola", 32),
                    ("Suat Kaya", "Sol Kanat", 7, 600000, "Türkiye", 25),
                    ("Atakan Akkaynak", "Merkez Orta Saha", 8, 700000, "Almanya", 25),
                    ("Mehdi Boudjemaa", "Ön Libero", 6, 800000, "Cezayir", 26),
                    ("Ferhat Yazgan", "Merkez Orta Saha", 10, 500000, "Türkiye", 31),
                    ("Zargo Touré", "Stoper", 4, 400000, "Senegal", 34),
                    ("Loïck Landre", "Stoper", 3, 500000, "Fransa", 32),
                    ("Kerem Kalafat", "Sağ Bek", 2, 600000, "Türkiye", 23),
                    ("Erkan Kaş", "Sol Bek", 33, 300000, "Türkiye", 33),
                    ("Hasan Hüseyin Akınay", "Kaleci", 1, 400000, "Türkiye", 31),
                    ("Ali Türkan", "Kaleci", 25, 200000, "Türkiye", 37),
                    ("Eren Karadağ", "Sol Kanat", 17, 400000, "Türkiye", 24),
                    ("Berkay Can Değirmencioğlu", "Stoper", 5, 300000, "Türkiye", 31),
                    ("Ozan Sol", "Sağ Kanat", 77, 400000, "Türkiye", 31),
                ]
            }
        }

        total_players_added = 0
        total_stats_added = 0

        for team_id, data in team_squads.items():
            team = Team.objects.filter(id=team_id).first()
            if not team:
                continue

            for name, pos, num, mv, nat, age in data["players"]:
                player, created = Player.objects.get_or_create(
                    name=name,
                    defaults={
                        "current_team": team,
                        "position": pos,
                        "jersey_number": num,
                        "market_value": Decimal(mv),
                        "nationality": nat,
                        "age": age,
                        "is_active": True,
                        "is_legend": False
                    }
                )
                if not created and player.current_team != team:
                    player.current_team = team
                    player.is_active = True
                    player.save()

                if created:
                    total_players_added += 1

                # Aktif sezon istatistiği
                st, st_created = PlayerSeasonStats.objects.get_or_create(
                    player=player,
                    season=active_season,
                    team=team,
                    defaults={
                        "matches": 8,
                        "goals": 2 if "Santrafor" in pos or "Kanat" in pos else (1 if "Orta" in pos else 0),
                        "assists": 2 if "Orta" in pos or "Kanat" in pos else 0,
                        "rating": 7.4 if "Santrafor" in pos else 7.2
                    }
                )
                if st_created:
                    total_stats_added += 1

        self.stdout.write(self.style.SUCCESS(
            f"BAŞARILI: {total_players_added} yeni aktif oyuncu, {total_stats_added} sezon istatistiği eklendi!"
        ))
