#from django-excel-templates/test/det_testproject/testapp/models.py
from django.db import models

class TestAllBaseTypes(models.Model):
    AutoField = models.AutoField(primary_key=True) # int
    BooleanField = models.BooleanField() # bool
    CharField = models.CharField(max_length=50) # unicode
    CommaSeparatedIntegerField = models.CommaSeparatedIntegerField(max_length=25) # unicode
    DateField = models.DateField(auto_now_add=True) # datetime.date
    DateTimeField = models.DateTimeField(auto_now_add=True) # datetime.datetime
    DecimalField = models.DecimalField(max_digits=10,decimal_places=2) # decimal.Decimal
    EmailField = models.EmailField(max_length=75) # unicode
    #FileField = models.FileField()
    #FilePathField = models.FilePathField()
    FloatField = models.FloatField() # float
    #ImageField = models.ImageField() 
    IntegerField = models.IntegerField() # int
    IPAddressField = models.IPAddressField() # unicode
    NullBooleanField = models.NullBooleanField() # bool
    PositiveIntegerField = models.PositiveIntegerField() # int
    PositiveSmallIntegerField = models.PositiveSmallIntegerField() # int
    SlugField = models.SlugField(max_length=30) # unicode
    SmallIntegerField = models.SmallIntegerField() # int
    TextField = models.TextField() # unicode
    TimeField = models.TimeField(auto_now_add=True) # datetime.time
    URLField = models.URLField(max_length=100) # unicode
    #XMLField = models.XMLField()
    def __unicode__(self):
        return u"%s" % (self.CharField)

