from django.db import models


class StandartModel(models.Model):
    '''Стандартная модель с текстом и датой (+ сортировка)'''
    text = models.TextField(null=True)
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-pub_date']
        abstract = True

    def __str__(self):
        return self.text[:15]
