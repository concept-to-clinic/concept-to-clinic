import json
import mimetypes
import os
import dicom
import base64
from backend.api import serializers
from backend.cases.models import (
    Case,
    Candidate,
    Nodule,
    CaseSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from backend.images.models import ImageSeries
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.decorators import renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = serializers.CaseSerializer


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = serializers.CandidateSerializer


class NoduleViewSet(viewsets.ModelViewSet):
    queryset = Nodule.objects.all()
    serializer_class = serializers.NoduleSerializer


class ImageSeriesViewSet(viewsets.ModelViewSet):
    queryset = ImageSeries.objects.all()
    serializer_class = serializers.ImageSeriesSerializer


class ImageMetadataApiView(APIView):   

    def _sanitise_unicode(self, s):
        return s.replace(u"\u0000", "").strip()

    def _convert_value(self, v):
        t = type(v)
        if t in (list, int, float):
            cv = v
        elif t == str:
            cv = self._sanitise_unicode(v)
        elif t == bytes:
            s = v.decode('ascii', 'replace')
            cv = self._sanitise_unicode(s)
        elif t == dicom.valuerep.DSfloat:
            cv = float(v)
        elif t == dicom.valuerep.IS:
            cv = int(v)
        elif t == dicom.valuerep.PersonName3:
            cv = str(v)
        else:
            cv = repr(v)
        return cv

    def dicom_dataset_to_dict(self, dicom_header):
        '''
        Put dicom metadata into a separate dictionary
        '''
        dicom_dict = {}
        repr(dicom_header)
        for dicom_value in dicom_header.values():
            if dicom_value.tag == (0x7fe0, 0x0010):
                # discard pixel data
                continue
            if type(dicom_value.value) == dicom.dataset.Dataset:
                dicom_dict[dicom_value.name] = self.dicom_dataset_to_dict(dicom_value.value)
            else:
                dicom_dict[dicom_value.name] = self._convert_value(dicom_value.value)
        return dicom_dict

    def get(self, request):
        '''
        Get metadata of a DICOM image including the image in base64 format.
        Example: .../api/images/metadata?dicom_location='FULL_PATH_TO_IMAGE'
        ---
        parameters:
            - name: dicom_location
            description: 'QUOTED' full location of the image
            required: true
            type: string
        '''
        path = request.GET.get('dicom_location')
        if path is None:
            raise Exception('dicom_location not provided')
        path = path[1:-1]   # un-quoting the string
        ds = dicom.read_file(path, force=True)
        return Response({
            'metadata': self.dicom_dataset_to_dict(ds),
            'image': base64.b64encode((ds.pixel_array.tostring()))
        })


class ImageAvailableApiView(APIView):
    """
    View list of images from dataset directory
    """

    def __init__(self, *args, **kwargs):
        super(ImageAvailableApiView, self).__init__(**kwargs)
        self.fss = FileSystemStorage(settings.DATASOURCE_DIR)

    @staticmethod
    def filename_to_dict(name, location):
        d = {
            'type': 'file',
            'mime_guess': mimetypes.guess_type(name)[0],
            'name': name,
            'path': os.path.join(location, name)
        }
        return d

    def walk(self, location, dir_name='/'):
        """
        Recursively walkthrough directories and files
        """
        folders, files = self.fss.listdir(location)
        tree = {'name': dir_name, 'children': []}
        tree['files'] = [self.filename_to_dict(filename, location) for filename in sorted(files)]
        tree['type'] = 'folder'
        tree['children'] = [self.walk(os.path.join(location, dir), dir) for dir in folders]
        return tree

    def get(self, request):
        """
        Return a sorted (by name) list of files and folders in dataset

        Format::

          {
            "directories": {
              "name": "/",
              "children": [
                {
                  "name": "LIDC-IDRI-0002",
                  "children": [
                    {
                      "name": "1.3.6.1.4.1.14519.5.2.1.6279.6001.490157381160200744295382098329",
                      "children": [
                        {
                          "name": "1.3.6.1.4.1.14519.5.2.1.6279.6001.619372068417051974713149104919",
                          "children": [],
                          "files": [
                            {
                              "type": "file",
                              "mime_guess": "application/dicom",
                              "name": "-80.750000.dcm",
                              "path": "/images/LIDC-IDRI-0002/1.3.[...snip...]3149104919/-80.750000.dcm"
                            },
                            {
                              "type": "file",
                              "mime_guess": "application/dicom",
                              "name": "-82.000000.dcm",
                              "path": "/images/LIDC-IDRI-0002/1.3.[...snip...]3149104919/-82.000000.dcm"
                            },
                            ...
                          ],
                          "type": "folder"
                        }
                      ],
                      "files": [],
                      "type": "folder"
                    }
                  ],
                  "files": [],
                  "type": "folder"
                }
              ],
              "files": [],
              "type": "folder"
            }
          }

        """
        tree = self.walk(settings.DATASOURCE_DIR)
        return Response({'directories': tree})


@api_view(['GET'])
def candidate_mark(request, candidate_id):
    return Response({'response': "Candidate {} was marked".format(candidate_id)})


@api_view(['GET'])
def candidate_dismiss(request, candidate_id):
    return Response({'response': "Candidate {} was dismissed".format(candidate_id)})


class JsonHtmlRenderer(renderers.BaseRenderer):
    media_type = 'text/html'
    format = 'html'

    def render(self, data, media_type=None, renderer_context=None):
        return "<pre>{}</pre>".format(json.dumps(data, indent=4, sort_keys=True, cls=DjangoJSONEncoder))


@api_view(['GET'])
# Render .json and .html requests
@renderer_classes((JSONRenderer, JsonHtmlRenderer))
def case_report(request, case_id, format=None):
    case = get_object_or_404(Case, pk=case_id)

    return Response(CaseSerializer(case).data)


@api_view(['POST'])
def nodule_update(request, nodule_id):
    try:
        lung_orientation = json.loads(request.body)['lung_orientation']
    except Exception as e:
        return Response({'response': "An error occurred: {}".format(e)}, 500)

    if lung_orientation is None:
        lung_orientation = 'NONE'

    orientation_choices = [orientation.name for orientation in Nodule.LungOrientation]

    if lung_orientation not in orientation_choices:
        return Response({'response': "ValueError: lung_orientation must be one of {}".format(orientation_choices)}, 500)

    Nodule.objects.filter(pk=nodule_id).update(lung_orientation=Nodule.LungOrientation[lung_orientation].value)
    return Response(
        {'response': "Lung orientation of nodule {} has been changed to '{}'".format(nodule_id, lung_orientation)})
