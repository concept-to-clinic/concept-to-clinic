from django.conf import settings


def git_version(request):
    return {'APP_VERSION_NUMBER': settings.APP_VERSION_NUMBER}
