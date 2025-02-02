import logging

# import time
from datetime import timedelta
from homeassistant import config_entries, core

# from homeassistant.core import callback
from homeassistant.helpers import entity_platform
from homeassistant.components.kodi.const import DATA_KODI, DOMAIN as KODI_DOMAIN
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST
from .media_sensor_event_manager import (
    MediaSensorEventManager,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_registry import async_get
import voluptuous as vol

from .const import (
    OPTION_HIDE_WATCHED,
    OPTION_SEARCH_EPISODES,
    OPTION_SEARCH_EPISODES_LIMIT,
    OPTION_SEARCH_SONGS,
    OPTION_SEARCH_SONGS_LIMIT,
    OPTION_SEARCH_ALBUMS,
    OPTION_SEARCH_ALBUMS_LIMIT,
    OPTION_SEARCH_ARTISTS,
    OPTION_SEARCH_ARTISTS_LIMIT,
    OPTION_SEARCH_MUSICVIDEOS,
    OPTION_SEARCH_MUSICVIDEOS_LIMIT,
    OPTION_SEARCH_MOVIES,
    OPTION_SEARCH_MOVIES_LIMIT,
    OPTION_SEARCH_TVSHOWS,
    OPTION_SEARCH_TVSHOWS_LIMIT,
    OPTION_SEARCH_CHANNELS_TV,
    OPTION_SEARCH_CHANNELS_TV_LIMIT,
    OPTION_SEARCH_CHANNELS_RADIO,
    OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_SONGS,
    OPTION_SEARCH_RECENTLY_ADDED_ALBUMS,
    OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS,
    OPTION_SEARCH_RECENTLY_ADDED_MOVIES,
    OPTION_SEARCH_RECENTLY_ADDED_EPISODES,
    OPTION_SEARCH_RECENTLY_PLAYED_LIMIT,
    OPTION_SEARCH_RECENTLY_PLAYED_SONGS,
    OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS,
    OPTION_SEARCH_KEEP_ALIVE_TIMER,
    DEFAULT_OPTION_SEARCH_SONGS,
    DEFAULT_OPTION_SEARCH_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_ALBUMS,
    DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_ARTISTS,
    DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_EPISODES,
    DEFAULT_OPTION_SEARCH_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_TV,
    DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_RADIO,
    DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    DEFAULT_OPTION_SEARCH_MUSICVIDEOS,
    DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT,
    DEFAULT_OPTION_SEARCH_MOVIES,
    DEFAULT_OPTION_SEARCH_MOVIES_LIMIT,
    DEFAULT_OPTION_SEARCH_TVSHOWS,
    DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS,
    DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS,
    DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_LIMIT,
    DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER,
    DOMAIN,
    KODI_DOMAIN_PLATFORM,
    CONF_SENSOR_RECENTLY_ADDED_TVSHOW,
    CONF_SENSOR_RECENTLY_ADDED_MOVIE,
    CONF_SENSOR_PLAYLIST,
    CONF_SENSOR_SEARCH,
    CONF_KODI_INSTANCE,
    ATTR_METHOD,
)
from .entities import (
    KodiRecentlyAddedMoviesEntity,
    KodiRecentlyAddedTVEntity,
)
from .entity_kodi_search import KodiSearchEntity
from .entity_kodi_playlist import KodiPlaylistEntity
from .utils import (
    find_matching_config_entry,
)

PLATFORM_SCHEMA = vol.Any(
    PLATFORM_SCHEMA.extend(
        {
            vol.Required(CONF_HOST): cv.string,
            vol.Optional(OPTION_HIDE_WATCHED, default=False): bool,
        }
    ),
)

KODI_MEDIA_SENSOR_CALL_METHOD_SCHEMA = cv.make_entity_service_schema(
    {vol.Required(ATTR_METHOD): cv.string}, extra=vol.ALLOW_EXTRA
)


SCAN_INTERVAL = timedelta(seconds=300)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    # _hass = hass
    conf = hass.data[DOMAIN][config_entry.entry_id]
    kodi_config_entry = find_matching_config_entry(hass, conf[CONF_KODI_INSTANCE])
    reg = async_get(hass)

    key = kodi_config_entry.unique_id
    if key == None:
        key = kodi_config_entry.entry_id

    kodi_entity_id = reg.async_get_entity_id(KODI_DOMAIN_PLATFORM, KODI_DOMAIN, key)

    try:
        data = hass.data[KODI_DOMAIN][conf[CONF_KODI_INSTANCE]]
    except KeyError:
        config_entries = [
            entry.as_dict() for entry in hass.config_entries.async_entries(KODI_DOMAIN)
        ]
        _LOGGER.error(
            "Failed to setup sensor. Could not find kodi data from existing config entries: %s",
            config_entries,
        )
        return

    kodi = data[DATA_KODI]
    sensorsList = list()
    event_manager = MediaSensorEventManager()

    if conf.get(CONF_SENSOR_RECENTLY_ADDED_TVSHOW):
        tv_entity = KodiRecentlyAddedTVEntity(
            kodi,
            kodi_config_entry.data,
            hide_watched=conf.get(OPTION_HIDE_WATCHED, False),
        )
        sensorsList.append(tv_entity)

    if conf.get(CONF_SENSOR_RECENTLY_ADDED_MOVIE):
        movies_entity = KodiRecentlyAddedMoviesEntity(
            kodi,
            kodi_config_entry.data,
            hide_watched=conf.get(OPTION_HIDE_WATCHED, False),
        )
        sensorsList.append(movies_entity)

    if conf.get(CONF_SENSOR_PLAYLIST):
        playlist_entity = KodiPlaylistEntity(
            hass,
            kodi,
            kodi_entity_id,
            kodi_config_entry.data,
            event_manager,
        )
        sensorsList.append(playlist_entity)

    if conf.get(CONF_SENSOR_SEARCH):
        search_entity = KodiSearchEntity(
            hass, kodi, kodi_entity_id, kodi_config_entry.data, event_manager
        )
        search_entity.set_search_songs(
            conf.get(OPTION_SEARCH_SONGS, DEFAULT_OPTION_SEARCH_SONGS)
        )
        search_entity.set_search_songs_limit(
            conf.get(OPTION_SEARCH_SONGS_LIMIT, DEFAULT_OPTION_SEARCH_SONGS_LIMIT)
        )
        search_entity.set_search_albums(
            conf.get(OPTION_SEARCH_ALBUMS, DEFAULT_OPTION_SEARCH_ALBUMS)
        )
        search_entity.set_search_albums_limit(
            conf.get(OPTION_SEARCH_ALBUMS_LIMIT, DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT)
        )

        search_entity.set_search_artists(
            conf.get(OPTION_SEARCH_ARTISTS, DEFAULT_OPTION_SEARCH_ARTISTS)
        )
        search_entity.set_search_artists_limit(
            conf.get(OPTION_SEARCH_ARTISTS_LIMIT, DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT)
        )

        search_entity.set_search_musicvideos(
            conf.get(OPTION_SEARCH_MUSICVIDEOS, DEFAULT_OPTION_SEARCH_MUSICVIDEOS)
        )

        search_entity.set_search_musicvideos_limit(
            conf.get(
                OPTION_SEARCH_MUSICVIDEOS_LIMIT, DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT
            )
        )

        search_entity.set_search_movies(
            conf.get(OPTION_SEARCH_MOVIES, DEFAULT_OPTION_SEARCH_MOVIES)
        )
        search_entity.set_search_movies_limit(
            conf.get(OPTION_SEARCH_MOVIES_LIMIT, DEFAULT_OPTION_SEARCH_MOVIES_LIMIT)
        )

        search_entity.set_search_tvshows(
            conf.get(OPTION_SEARCH_TVSHOWS, DEFAULT_OPTION_SEARCH_TVSHOWS)
        )
        search_entity.set_search_tvshows_limit(
            conf.get(OPTION_SEARCH_TVSHOWS_LIMIT, DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT)
        )

        search_entity.set_search_episodes(
            conf.get(OPTION_SEARCH_EPISODES, DEFAULT_OPTION_SEARCH_EPISODES)
        )
        search_entity.set_search_episodes_limit(
            conf.get(OPTION_SEARCH_EPISODES_LIMIT, DEFAULT_OPTION_SEARCH_EPISODES_LIMIT)
        )

        search_entity.set_search_channels_tv(
            conf.get(OPTION_SEARCH_CHANNELS_TV, DEFAULT_OPTION_SEARCH_CHANNELS_TV)
        )
        search_entity.set_search_channels_tv_limit(
            conf.get(
                OPTION_SEARCH_CHANNELS_TV_LIMIT, DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT
            )
        )

        search_entity.set_search_channels_radio(
            conf.get(OPTION_SEARCH_CHANNELS_RADIO, DEFAULT_OPTION_SEARCH_CHANNELS_RADIO)
        )
        search_entity.set_search_channels_radio_limit(
            conf.get(
                OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
                DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
            )
        )

        search_entity.set_search_recently_played_limit(
            conf.get(
                OPTION_SEARCH_RECENTLY_PLAYED_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_LIMIT,
            )
        )

        search_entity.set_search_recently_played_songs(
            conf.get(
                OPTION_SEARCH_RECENTLY_PLAYED_SONGS,
                DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS,
            )
        )
        search_entity.set_search_recently_played_albums(
            conf.get(
                OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS,
                DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS,
            )
        )

        search_entity.set_search_recently_added_limit(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_LIMIT,
            )
        )

        search_entity.set_search_recently_added_songs(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_SONGS,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS,
            )
        )
        search_entity.set_search_recently_added_albums(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_ALBUMS,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS,
            )
        )
        search_entity.set_search_recently_added_movies(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_MOVIES,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES,
            )
        )

        search_entity.set_search_recently_added_musicvideos(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS,
            )
        )
        search_entity.set_search_recently_added_episodes(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_EPISODES,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES,
            )
        )
        search_entity.set_search_keep_alive_timer(
            conf.get(
                OPTION_SEARCH_KEEP_ALIVE_TIMER, DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER
            )
        )
        sensorsList.append(search_entity)

    async_add_entities(sensorsList, update_before_add=True)

    # Register the services
    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        "call_method", KODI_MEDIA_SENSOR_CALL_METHOD_SCHEMA, "async_call_method"
    )


async def async_setup_platform(
    hass: core.HomeAssistant, config: dict, async_add_entities, discovery_info=None
) -> None:
    """Setup sensors from yaml configuration."""

    _LOGGER.warning("Configuration using yaml files is not supported")
