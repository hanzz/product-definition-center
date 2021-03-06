#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
from django.db import models
from jsonfield import JSONField
from pdc.apps.package.models import RPM


class UnreleasedVariant(models.Model):
    # Not the variant from compose ... which back references compose
    variant_id          = models.CharField(max_length=100, blank=False)
    variant_uid         = models.CharField(max_length=200, blank=False)
    variant_name        = models.CharField(max_length=300, blank=False)
    variant_type        = models.CharField(max_length=100, blank=False)
    # variant_version/_release are _not_ distribution versions/releases
    variant_version     = models.CharField(max_length=100, blank=False)
    variant_release     = models.CharField(max_length=100, blank=False)
    active              = models.BooleanField(default=False)
    koji_tag            = models.CharField(max_length=300, blank=False)
    modulemd            = models.TextField(blank=False)
    rpms                = models.ManyToManyField(RPM)

    class Meta:
        ordering = ("variant_uid", "variant_version", "variant_release")
        unique_together = (
            ("variant_uid", "variant_version", "variant_release"),
        )

    def __unicode__(self):
        return u"%s" % (self.variant_uid, )

    def export(self):
        result = {
            'variant_id': self.variant_id,
            'variant_uid': self.variant_uid,
            'variant_name': self.variant_name,
            'variant_type': self.variant_type,
            'variant_version': self.variant_version,
            'variant_release': self.variant_release,
            'active': self.active,
            'koji_tag': self.koji_tag,
            'modulemd': self.modulemd,
            'runtime_deps': [v.dependency for v in self.runtime_deps.all()],
            'build_deps': [v.dependency for v in self.build_deps.all()],
        }

        result["rpms"] = []
        objects = self.rpms.all()
        for obj in objects:
            result["rpms"].append(obj.export())

        return result


class VariantDependency(models.Model):

    dependency = models.CharField(max_length=300)
    stream = models.CharField(max_length=300)

    class Meta:
        abstract = True


class RuntimeDependency(VariantDependency):

    variant = models.ForeignKey("UnreleasedVariant",
                                related_name="runtime_deps")


class BuildDependency(VariantDependency):

    variant = models.ForeignKey("UnreleasedVariant",
                                related_name="build_deps")


class Tree(models.Model):
    tree_id             = models.CharField(max_length=200, unique=True)
    tree_date           = models.DateField()
    arch                = models.ForeignKey("common.Arch", related_name="+")
    variant             = models.ForeignKey(UnreleasedVariant)
    dt_imported         = models.DateTimeField(auto_now_add=True)
    deleted             = models.BooleanField(default=False)
    content             = JSONField()
    content_format      = models.ManyToManyField('repository.ContentFormat')
    url                 = models.CharField(max_length=255)  # Currently just some local path

    class Meta:
        ordering = ("tree_id",)

    def export(self):
        return {
            "tree_id": self.tree_id,
            "tree_date": self.tree_date.isoformat(),
            "arch": self.arch.name,
            "variant": {
                'variant_uid': self.variant.variant_uid,
                'variant_version': self.variant.variant_version,
                'variant_release': self.variant.variant_release,
                'active': self.variant.active,
            },
            "deleted": self.deleted,
            "content": self.content,
            "content_format": [item.name for item in self.content_format.all()],
            "url": self.url,
        }

    def __unicode__(self):
        return u"%s" % self.tree_id
