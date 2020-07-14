from django.apps import AppConfig


def user_default_group(sender, instance, **kwargs):
    """
    Adds new user to ReadOnly Group on save
    :param sender: sender model
    :param instance: user that was saved
    :param kwargs:
    """

    from django.contrib.auth.models import Group

    if kwargs["created"]:
        group = Group.objects.get(name='ReadOnly')
        instance.groups.add(group)


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from django.db.models.signals import post_save
        from django.contrib.auth import get_user_model

        post_save.connect(user_default_group, sender=get_user_model())
