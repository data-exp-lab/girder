import _ from 'underscore';

import PluginConfigBreadcrumbWidget from 'girder/views/widgets/PluginConfigBreadcrumbWidget';
import View from 'girder/views/View';
import events from 'girder/events';
import { restRequest } from 'girder/rest';

import ConfigViewTemplate from '../templates/configView.pug';
import '../stylesheets/configView.styl';

var ConfigView = View.extend({
    events: {
        'submit #g-mongo-search-settings-form': function (event) {
            event.preventDefault();

            this.$('#g-mongo-search-error-message').empty();

            this._saveSettings([{
                key: 'mongo_search.allowed',
                value: this.$('#g-mongo-search').val().trim()
            }]);
        },
        'click #g-mongo-search-defaults': function (event) {
            event.preventDefault();

            restRequest({
                type: 'GET',
                path: '/resource/mongo_search/allowed',
                data: {
                    'default': true
                }
            }).done(_.bind(function (resp) {
                this.allowed = resp;
                this.render();
            }, this));
        }
    },

    initialize: function () {
        restRequest({
            type: 'GET',
            path: 'system/setting',
            data: {
                list: JSON.stringify(['mongo_search.allowed'])
            }
        }).done(_.bind(function (resp) {
            this.allowed = resp['mongo_search.allowed'];
            this.render();
        }, this));
    },

    render: function () {
        this.$el.html(ConfigViewTemplate({
            allowed: JSON.stringify(this.allowed, null, 4)
        }));

        this.breadcrumb = new PluginConfigBreadcrumbWidget({
            pluginName: 'MongoDB custom search',
            el: this.$('.g-config-breadcrumb-container'),
            parentView: this
        }).render();

        return this;
    },

    _saveSettings: function (settings) {
        restRequest({
            type: 'PUT',
            path: 'system/setting',
            data: {
                list: JSON.stringify(settings)
            },
            error: null
        }).done(_.bind(function () {
            events.trigger('g:alert', {
                icon: 'ok',
                text: 'Settings saved.',
                type: 'success',
                timeout: 3000
            });
        }, this)).error(_.bind(function (resp) {
            this.$('#g-mongo-search-error-message').text(
                resp.responseJSON.message
            );
        }, this));
    }
});

export default ConfigView;
