from django.db import models


# Create your models here.

# ---------------------------------------------------------------------------
# Contact - US
# ---------------------------------------------------------------------------
class ContactMessage(models.Model):
    """A message submitted via the 'Contact us' form."""

    name = models.CharField('نام', max_length=80)
    email = models.EmailField('ایمیل', blank=True)
    message = models.TextField('پیام')
    is_read = models.BooleanField('خوانده شده', default=False)
    created_at = models.DateTimeField('تاریخ دریافت', auto_now_add=True)

    class Meta:
        verbose_name = 'پیام تماس'
        verbose_name_plural = 'پیام‌های تماس'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} — {self.created_at:%Y/%m/%d %H:%M}'