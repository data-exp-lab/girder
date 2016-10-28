import router from 'girder/router';
import events from 'girder/events';
import { exposePluginConfig } from 'girder/utilities/PluginUtils';

exposePluginConfig('mongo_search', 'plugins/mongo_search/config');

import ConfigView from './views/ConfigView';
router.route('plugins/mongo_search/config', 'mongoSearchConfig', function () {
       events.trigger('g:navigateTo', ConfigView);
});

