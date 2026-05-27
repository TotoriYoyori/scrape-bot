from src.scraper import ScrapeBot
from src.scraper.routines.audible import AudibleRoutine
from src.scraper.routines.jason_thoughtleader import JasonThoughtleaderRoutine

# =============== ASSEMBLE SCRAPING ROBOT ===============
bot = ScrapeBot(
    name="Audible Scrape Bot",
    description="Scrapes the Audible home page to collect book information.",
)

routine = AudibleRoutine(target_category="Money & Finance")

bot.install_routine(routine)

bot.run()
