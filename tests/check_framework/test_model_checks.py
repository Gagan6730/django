from django.core import checks
from django.core.checks import Error
from django.db import models
from django.test import SimpleTestCase
from django.test.utils import (
    isolate_apps, modify_settings, override_system_checks,
)


@isolate_apps('check_framework', attr_name='apps')
@override_system_checks([checks.model_checks.check_all_models])
class DuplicateDBTableTests(SimpleTestCase):
    def test_collision_in_same_app(self):
        class Model1(models.Model):
            class Meta:
                db_table = 'test_table'

        class Model2(models.Model):
            class Meta:
                db_table = 'test_table'

        self.assertEqual(checks.run_checks(app_configs=self.apps.get_app_configs()), [
            Error(
                "db_table 'test_table' is used by multiple models: "
                "check_framework.Model1, check_framework.Model2.",
                obj='test_table',
                id='models.E028',
            )
        ])

    @modify_settings(INSTALLED_APPS={'append': 'basic'})
    @isolate_apps('basic', 'check_framework', kwarg_name='apps')
    def test_collision_across_apps(self, apps):
        class Model1(models.Model):
            class Meta:
                app_label = 'basic'
                db_table = 'test_table'

        class Model2(models.Model):
            class Meta:
                app_label = 'check_framework'
                db_table = 'test_table'

        self.assertEqual(checks.run_checks(app_configs=apps.get_app_configs()), [
            Error(
                "db_table 'test_table' is used by multiple models: "
                "basic.Model1, check_framework.Model2.",
                obj='test_table',
                id='models.E028',
            )
        ])

    def test_no_collision_for_unmanaged_models(self):
        class Unmanaged(models.Model):
            class Meta:
                db_table = 'test_table'
                managed = False

        class Managed(models.Model):
            class Meta:
                db_table = 'test_table'

        self.assertEqual(checks.run_checks(app_configs=self.apps.get_app_configs()), [])

    def test_no_collision_for_proxy_models(self):
        class Model(models.Model):
            class Meta:
                db_table = 'test_table'

        class ProxyModel(Model):
            class Meta:
                proxy = True

        self.assertEqual(Model._meta.db_table, ProxyModel._meta.db_table)
        self.assertEqual(checks.run_checks(app_configs=self.apps.get_app_configs()), [])
