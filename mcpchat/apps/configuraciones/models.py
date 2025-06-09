from django.db import models
from django.core.cache import cache

# Create your models here.
class SingletonConfiguracion(models.Model):

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        pass

    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonConfiguracion, self).save(*args, **kwargs)

        self.set_cache()

    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            if not created:
                obj.set_cache()
        return cache.get(cls.__name__)


class Configuraciones(SingletonConfiguracion):

    system_prompt = models.CharField(max_length=500)
    temperature = models.DecimalField(max_digits=10, decimal_places=2)
    dark_mode = models.BooleanField(default=False)
    llms = (
        ('groq', 'qwen-qwq-32b'),
        ('antro', 'claude-opus-4-20250514')
    )

    llm = models.CharField(
        max_length=5,
        choices=llms,
        default='groq', # valor por defecto
    )

    class Meta:
        verbose_name_plural = "Configuraciones"

    def __str__(self):
        return "Configuraciones"