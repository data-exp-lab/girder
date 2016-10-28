#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import bson.json_util

from girder import events
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import Resource, RestException
from girder.constants import AccessType, SettingDefault
from girder.models.model_base import ValidationException
from girder.utility import setting_utilities
from girder.utility.model_importer import ModelImporter

from .constants import PluginSettings, PluginSettingsDefaults


@setting_utilities.validator(PluginSettings.ALLOWED_FIELDS)
def validateAllowedFields(doc):
    val = doc['value']
    if not isinstance(val, dict):
        raise ValidationException('Allowed fields settings must be a dict.', 'value')

    # TODO: should be configurable too
    colls = set(['user', 'collection', 'folder', 'item'])

    if not all(_ in colls for _ in doc['value']):
        raise ValidationException('Only {} are valid keywords'.format(str(colls)),
                                  'value')
    if not all(isinstance(_, list) for _ in doc['value'].values()):
        raise ValidationException('Allowed fields values must be lists.', 'value')

    for coll in colls:
        model = ModelImporter().model(coll)
        keys = set(model._filterKeys[AccessType.READ])  # TODO: should it be SITE_ADMIN?
        if not all(_ in keys for _ in doc['value'][coll]):
            raise ValidationException('Invalid key for "{}"'.format(coll), 'value')


class ResourceExt(Resource):
    @access.public
    @describeRoute(
        Description('Run any search against a set of mongo collections.')
        .notes('Results will be filtered by permissions.')
        .param('type', 'The name of the collection to search, e.g. "item".')
        .param('q', 'The search query as a JSON object.')
        .param('limit', "Result set size limit (default=50).", required=False,
               dataType='int')
        .param('offset', "Offset into result set (default=0).", required=False,
               dataType='int')
        .errorResponse()
    )
    def mongoSearch(self, params):
        self.requireParams(('type', 'q'), params)
        allowed = ModelImporter.model('setting').get(PluginSettings.ALLOWED_FIELDS)
        limit, offset, sort = self.getPagingParameters(params, 'name')
        coll = params['type']

        events.trigger('mongo_search.allowed_collections', info=allowed)

        if coll not in allowed:
            raise RestException('Invalid resource type: %s' % coll)

        try:
            query = bson.json_util.loads(params['q'])
        except ValueError:
            raise RestException('The query parameter must be a JSON object.')

        model = ModelImporter().model(coll)
        if hasattr(model, 'filterResultsByPermission'):
            cursor = model.find(
                query, fields=allowed[coll] + ['public', 'access'])
            return list(model.filterResultsByPermission(
                cursor, user=self.getCurrentUser(), level=AccessType.READ,
                limit=limit, offset=offset, removeKeys=('public', 'access')))
        else:
            return list(model.find(query, fields=allowed[coll], limit=limit,
                                   offset=offset))

    @access.admin
    @describeRoute(
        Description('Get list of searchable fields per collection type.')
        .param('default', 'Whether to return the default list of searchable fields.',
               required=False, dataType='boolean', default=False)
    )
    def getAllowedFields(self, params):
        """
        Get list of searchable fields per collection type.
        """
        if self.boolParam('default', params, default=False):
            return SettingDefault.defaults[PluginSettings.ALLOWED_FIELDS]
        else:
            return self.model('setting').get(PluginSettings.ALLOWED_FIELDS)


def load(info):
    ext = ResourceExt()
    info['apiRoot'].resource.route('GET', ('mongo_search',), ext.mongoSearch)
    info['apiRoot'].resource.route('GET', ('mongo_search', 'allowed'),
                                   ext.getAllowedFields)

    # Add default allowed fields settings
    SettingDefault.defaults[PluginSettings.ALLOWED_FIELDS] = \
        PluginSettingsDefaults.defaults[PluginSettings.ALLOWED_FIELDS]
