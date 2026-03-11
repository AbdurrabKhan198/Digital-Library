"""
Management command to seed initial data for the Islamic Digital Library.

Creates knowledge domains, categories, languages, and notable scholars.
"""

from django.core.management.base import BaseCommand
from library.models import Category, Language, KnowledgeDomain, Scholar


class Command(BaseCommand):
    help = "Seed the database with knowledge domains, categories, languages, and scholars"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding initial data...")

        # =================================================================
        # KNOWLEDGE DOMAINS
        # =================================================================
        self.stdout.write("\n📂 Knowledge Domains:")
        religious, _ = KnowledgeDomain.objects.get_or_create(
            name="Religious Knowledge",
            defaults={
                "description": "Traditional Islamic religious sciences — Qur'an, Hadith, Fiqh, Aqeedah, and more.",
                "icon": "📖",
                "order": 1,
            }
        )
        self._log(religious, _)

        sciences, _ = KnowledgeDomain.objects.get_or_create(
            name="Islamic Sciences",
            defaults={
                "description": "Muslim contributions to worldly knowledge — Astronomy, Mathematics, Medicine, and more.",
                "icon": "🔬",
                "order": 2,
            }
        )
        self._log(sciences, _)

        # =================================================================
        # RELIGIOUS KNOWLEDGE CATEGORIES
        # =================================================================
        self.stdout.write("\n📖 Religious Knowledge Categories:")
        religious_categories = [
            {"name": "Qur'an", "description": "The Holy Qur'an — recitations, translations, and manuscripts.", "order": 1},
            {"name": "Tafsir", "description": "Qur'anic exegesis and commentary by renowned scholars.", "order": 2},
            {"name": "Hadith", "description": "Collections of Prophetic traditions (ahadith).", "order": 3},
            {"name": "Fiqh", "description": "Islamic jurisprudence across major schools of thought.", "order": 4},
            {"name": "Aqeedah", "description": "Islamic creed and theology.", "order": 5},
            {"name": "Seerah", "description": "Biography of the Prophet Muhammad ﷺ.", "order": 6},
            {"name": "Islamic History", "description": "History of Islam, caliphates, and Muslim civilizations.", "order": 7},
            {"name": "Arabic Language", "description": "Arabic grammar, morphology, and rhetoric.", "order": 8},
        ]

        for cat_data in religious_categories:
            cat, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={**cat_data, "knowledge_domain": religious}
            )
            # Update existing categories to link to domain if not linked
            if not created and not cat.knowledge_domain:
                cat.knowledge_domain = religious
                cat.save(update_fields=["knowledge_domain"])
            self._log(cat, created)

        # =================================================================
        # ISLAMIC SCIENCES CATEGORIES
        # =================================================================
        self.stdout.write("\n🔬 Islamic Sciences Categories:")
        sciences_categories = [
            {"name": "Astronomy", "description": "Islamic contributions to celestial observation, star catalogues, and cosmology.", "order": 1},
            {"name": "Mathematics", "description": "Algebra, geometry, trigonometry, and number theory from Muslim mathematicians.", "order": 2},
            {"name": "Medicine", "description": "Medical texts and pharmacology from Islamic golden age physicians.", "order": 3},
            {"name": "Physics", "description": "Mechanics, optics experiments, and physical theories by Muslim scientists.", "order": 4},
            {"name": "Chemistry", "description": "Alchemy, chemical processes, and distillation — foundations of modern chemistry.", "order": 5},
            {"name": "Philosophy", "description": "Islamic philosophy, logic, and metaphysics from Muslim thinkers.", "order": 6},
            {"name": "Geography", "description": "Cartography, travel accounts, and geographical treatises.", "order": 7},
            {"name": "Engineering", "description": "Mechanical devices, hydraulics, and architectural innovations.", "order": 8},
            {"name": "Optics", "description": "Scientific study of light, vision, and optical instruments.", "order": 9},
            {"name": "Logic", "description": "Formal logic, dialectics, and analytical reasoning.", "order": 10},
        ]

        for cat_data in sciences_categories:
            cat, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={**cat_data, "knowledge_domain": sciences}
            )
            if not created and not cat.knowledge_domain:
                cat.knowledge_domain = sciences
                cat.save(update_fields=["knowledge_domain"])
            self._log(cat, created)

        # =================================================================
        # LANGUAGES
        # =================================================================
        self.stdout.write("\n🌍 Languages:")
        languages = [
            {"name": "Arabic", "code": "ar"},
            {"name": "English", "code": "en"},
            {"name": "Urdu", "code": "ur"},
            {"name": "French", "code": "fr"},
            {"name": "Turkish", "code": "tr"},
            {"name": "Malay", "code": "ms"},
            {"name": "Indonesian", "code": "id"},
            {"name": "Bengali", "code": "bn"},
            {"name": "Latin", "code": "la"},
            {"name": "Persian", "code": "fa"},
        ]

        for lang_data in languages:
            lang, created = Language.objects.get_or_create(
                name=lang_data["name"],
                defaults=lang_data
            )
            self._log(lang, created)

        # =================================================================
        # NOTABLE ISLAMIC SCIENCE SCHOLARS
        # =================================================================
        self.stdout.write("\n👤 Notable Islamic Scientists:")
        scholars = [
            {
                "name": "Ibn Sina (Avicenna)",
                "birth_year": 980, "death_year": 1037,
                "field_of_expertise": "Medicine",
                "bio": "Persian polymath regarded as the father of early modern medicine. "
                       "Author of 'The Canon of Medicine', the standard medical textbook for centuries."
            },
            {
                "name": "Al-Khwarizmi",
                "birth_year": 780, "death_year": 850,
                "field_of_expertise": "Mathematics",
                "bio": "Persian mathematician, astronomer, and geographer. "
                       "Father of algebra — the word 'algorithm' derives from his name."
            },
            {
                "name": "Al-Biruni",
                "birth_year": 973, "death_year": 1048,
                "field_of_expertise": "Astronomy",
                "bio": "Polymath who contributed to astronomy, mathematics, geography, and anthropology. "
                       "Accurately calculated Earth's circumference."
            },
            {
                "name": "Ibn Rushd (Averroes)",
                "birth_year": 1126, "death_year": 1198,
                "field_of_expertise": "Philosophy",
                "bio": "Andalusian philosopher, physician, and jurist. "
                       "Known for commentaries on Aristotle that influenced European thought."
            },
            {
                "name": "Ibn al-Haytham (Alhazen)",
                "birth_year": 965, "death_year": 1040,
                "field_of_expertise": "Optics",
                "bio": "Father of modern optics. His 'Book of Optics' revolutionized understanding of "
                       "light, vision, and the scientific method."
            },
            {
                "name": "Jabir ibn Hayyan",
                "birth_year": 721, "death_year": 815,
                "field_of_expertise": "Chemistry",
                "bio": "Known as the father of chemistry (alchemy). Introduced experimental methodology "
                       "and numerous chemical processes still used today."
            },
            {
                "name": "Al-Idrisi",
                "birth_year": 1100, "death_year": 1165,
                "field_of_expertise": "Geography",
                "bio": "Arab geographer and cartographer who created the famous 'Tabula Rogeriana', "
                       "one of the most advanced world maps of the medieval era."
            },
            {
                "name": "Al-Jazari",
                "birth_year": 1136, "death_year": 1206,
                "field_of_expertise": "Engineering",
                "bio": "Polymath inventor and mechanical engineer. Author of 'The Book of Knowledge "
                       "of Ingenious Mechanical Devices', a masterpiece of engineering."
            },
        ]

        for s_data in scholars:
            scholar, created = Scholar.objects.get_or_create(
                name=s_data["name"],
                defaults=s_data
            )
            self._log(scholar, created)

        # =================================================================
        # BACKFILL: ensure existing books get the "Religious Knowledge" domain
        # =================================================================
        from library.models import Book
        updated = Book.objects.filter(knowledge_domain__isnull=True).update(
            knowledge_domain=religious
        )
        if updated:
            self.stdout.write(f"\n🔄 Backfilled {updated} existing book(s) → Religious Knowledge")

        self.stdout.write(self.style.SUCCESS("\n✨ Seeding complete!"))

    def _log(self, obj, created):
        status = "✅ Created" if created else "⏭️  Exists"
        self.stdout.write(f"  {status}: {obj}")
