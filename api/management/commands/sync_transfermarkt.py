from django.core.management.base import BaseCommand
from api.integrations import TransfermarktScraper
from api.models import Team


class Command(BaseCommand):
    help = "Transfermarkt uzerinden Super Lig kulupleri, kadrolari ve transferleri senkronize eder (Web Scraping)."

    def add_arguments(self, parser):
        parser.add_argument('--teams', action='store_true', help="Sadece Super Lig kuluplerini ve degerlerini guncelle")
        parser.add_argument('--transfers', action='store_true', help="Sadece Super Lig transferlerini guncelle")
        parser.add_argument('--squads', action='store_true', help="Kuluplerin oyuncu kadrolarini guncelle")

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("[INFO] Transfermarkt Web Scraping baslatiliyor..."))

        do_all = not (options['teams'] or options['transfers'] or options['squads'])

        if do_all or options['teams']:
            self.stdout.write("1. Super Lig kulupleri taraniyor...")
            teams = TransfermarktScraper.scrape_super_lig_teams()
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(teams)} kulup guncellendi."))

        if do_all or options['transfers']:
            self.stdout.write("2. Super Lig transferleri taraniyor...")
            transfers = TransfermarktScraper.scrape_super_lig_transfers()
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(transfers)} transfer guncellendi."))

        if do_all or options['squads']:
            self.stdout.write("3. Kulup kadrolari taraniyor...")
            super_teams = Team.objects.filter(is_super_lig=True)[:5]
            total_players = 0
            for t in super_teams:
                p_list = TransfermarktScraper.scrape_team_squad(t)
                total_players += len(p_list)
            self.stdout.write(self.style.SUCCESS(f"[OK] {total_players} oyuncu kadrosu guncellendi."))

        self.stdout.write(self.style.SUCCESS("[DONE] Transfermarkt senkronizasyonu tamamlandi!"))
