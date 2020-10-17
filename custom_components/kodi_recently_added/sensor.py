import logging
from typing import Optional

from homeassistant import config_entries, core
from homeassistant.components.kodi.const import DATA_KODI, DOMAIN as KODI_DOMAIN
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import CONF_HIDE_WATCHED, DOMAIN
from .entities import KodiRecentlyAddedMoviesEntity, KodiRecentlyAddedTVEntity

# PLATFORM_SCHEMA = vol.Any(
#    PLATFORM_SCHEMA.extend(
#        {
#            vol.Required(CONF_HOST): cv.string,
#            vol.Optional(CONF_HIDE_WATCHED, default=False): bool,
#        }
#    ),
# )
_LOGGER = logging.getLogger(__name__)


def find_matching_config_entry(
    hass: core.HomeAssistant, entry_id: str
) -> Optional[ConfigEntry]:
    """Search existing config entries for one matching the host."""
    for entry in hass.config_entries.async_entries(KODI_DOMAIN):
        # Skip any entry whose source is marked as ignored.
        if entry.entry_id == entry_id and entry.source != "ignore":
            return entry
    return None


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Defer sensor setup to the sensor manager."""
    conf = hass.data[DOMAIN][config_entry.entry_id]
    config_entry = find_matching_config_entry(hass, conf["kodi_config_entry_id"])
    try:
        data = hass.data[KODI_DOMAIN][conf["kodi_config_entry_id"]]
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

    tv_entity = KodiRecentlyAddedTVEntity(kodi, config_entry.data, hide_watched=False)
    movies_entity = KodiRecentlyAddedMoviesEntity(
        kodi, config_entry.data, hide_watched=False
    )
    async_add_entities([tv_entity, movies_entity])
