"""
``python manage.py seed_demo`` – populate the DB with starter categories and
a couple of sample manual articles so the site isn't empty on first run.

This is *optional* – the project works fine without it. Useful for a quick
demo / university presentation.

Usage:
    python manage.py seed_demo
"""

import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.news.models import Article, Category


# Starter categories with Persian keywords used by the smart categoriser.
DEFAULT_CATEGORIES = [
    {
        'name': 'سیاسی',
        'slug': 'political',
        'color': 'bg-red-500/20 text-red-300',
        'keywords': 'سیاسی, دولت, مجلس, انتخابات, رئیس جمهور, وزارت, حکومت, سیاست',
    },
    {
        'name': 'اقتصادی',
        'slug': 'economic',
        'color': 'bg-emerald-500/20 text-emerald-300',
        'keywords': 'اقتصاد, دلار, بورس, تورم, نفت, بازرگانی, صنعت, بانک, مالی',
    },
    {
        'name': 'ورزشی',
        'slug': 'sports',
        'color': 'bg-orange-500/20 text-orange-300',
        'keywords': 'فوتبال, والیبال, بسکتبال, ورزش, المپیک, تیم ملی, لیگ, بازی, بازیکن, مربی',
    },
    {
        'name': 'فناوری',
        'slug': 'technology',
        'color': 'bg-sky-500/20 text-sky-300',
        'keywords': 'فناوری, تکنولوژی, هوش مصنوعی, اینترنت, کامپیوتر, گوشی, نرم افزار, برنامه, دیجیتال',
    },
    {
        'name': 'فرهنگی',
        'slug': 'culture',
        'color': 'bg-purple-500/20 text-purple-300',
        'keywords': 'فرهنگ, هنر, سینما, موسیقی, تئاتر, کتاب, ادبیات, فیلم',
    },
    {
        'name': 'بین‌الملل',
        'slug': 'world',
        'color': 'bg-cyan-500/20 text-cyan-300',
        'keywords': 'جهان, بین الملل, آمریکا, اروپا, چین, روسیه, اوکراین, سازمان ملل',
    },
]


class Command(BaseCommand):
    help = 'Seed starter categories and a few demo articles.'

    def handle(self, *args, **options):
        created_cats = []
        for data in DEFAULT_CATEGORIES:
            obj, created = Category.objects.get_or_create(
                slug=data['slug'],
                defaults=data,
            )
            created_cats.append(obj)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  + category: {obj.name}'))
            else:
                self.stdout.write(f'  = category exists: {obj.name}')

        # Add a couple of manual demo articles only if the DB is empty.
        if Article.objects.count() == 0:
            samples = [
                {
                    'title': 'آغاز هم‌اندیشی اقتصاد دیجیتال با حضور کارشناسان حوزه فناوری',
                    'summary': 'نخبگان حوزه فناوری و اقتصاد برای بررسی فرصت‌های رشد دیجیتال گرد هم آمدند.',
                    'content': 'به گزارش خبرگزاری ما، نخستین نشست هم‌اندیشی اقتصاد دیجیتال امروز با حضور کارشناسان برجسته برگزار شد. در این نشست مسائل مربوط به هوش مصنوعی، نوآوری و کارآفرینی دیجیتال مورد بررسی قرار گرفت.',
                    'category_slug': 'technology',
                    'is_featured': True,
                },
                {
                    'title': 'تیم ملی فوتبال با بردی پرگل برابر حریف به جام صعود کرد',
                    'summary': 'بازیکنان تیم ملی با درخشش در نیمه دوم به برتری پرگل دست یافتند.',
                    'content': 'تیم ملی فوتبال کشورمان در دیداری حساس توانست با نتیجه پرگل حریف خود را شکست دهد و به مرحله بعدی جام صعود کند. این برد باعث شادی هزاران هوادار شد.',
                    'category_slug': 'sports',
                    'is_featured': True,
                },
                {
                    'title': 'نشست مشترک دولت و بخش خصوصی برای کنترل تورم',
                    'summary': 'اقتصاددانان و نمایندگان اتاق بازرگانی راهکارهای مهار تورم را بررسی کردند.',
                    'content': 'در نشست مشترک امروز، مسائل کلان اقتصادی و راهکارهای کنترل تورم مورد گفت‌وگو قرار گرفت. کارشناسان بر لزوم همکاری دولت و بخش خصوصی تأکید کردند.',
                    'category_slug': 'economic',
                    'is_featured': True,
                },
            ]
            cats_by_slug = {c.slug: c for c in created_cats}
            for s in samples:
                Article.objects.create(
                    title=s['title'],
                    summary=s['summary'],
                    content=s['content'],
                    category=cats_by_slug.get(s['category_slug']),
                    is_published=True,
                    is_featured=s.get('is_featured', False),
                    is_rss=False,
                    published_at=timezone.now(),
                )
            self.stdout.write(self.style.SUCCESS(f'  + created {len(samples)} demo articles'))

        self.stdout.write(self.style.SUCCESS('Seed complete.'))
