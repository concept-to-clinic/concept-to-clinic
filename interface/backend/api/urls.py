from backend.api.views import (
    CaseViewSet,
    CandidateViewSet,
    NoduleViewSet,
    ImageSeriesViewSet,
    ImageAvailableApiView,
    ImageMetadataApiView,
    case_report,
    update_candidate_location,
    candidates_info,
    image_series_registration,
    case_available,
    case_create
)
from django.conf.urls import (
    include,
    url
)
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

router = routers.DefaultRouter()
router.register(r'cases', CaseViewSet)
router.register(r'candidates', CandidateViewSet)
router.register(r'nodules', NoduleViewSet)
router.register(r'images', ImageSeriesViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^cases/available$', case_available, name='cases-available'),
    url(r'^cases/create$', case_create, name='cases-create'),
    url(r'^images/available$', ImageAvailableApiView.as_view(), name='images-available'),
    url(r'^images/metadata$', ImageMetadataApiView.as_view(), name='images-metadata'),
    url(r'^candidates-info$', candidates_info, name='candidates-info'),
    url(r'^images/image_series_registration$', image_series_registration, name='images-registration'),
    url(r'^candidates/(?P<candidate_id>\d+)/move$', update_candidate_location, name='update-candidate-location'),
]

# Support different suffixes
urlpatterns += format_suffix_patterns([url(r'^cases/(?P<pk>\d+)/report$', case_report, name='case-report')])
