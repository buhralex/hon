from __future__ import annotations

from pyhon import HonConnection
from pyhon.parameter import HonParameterRange

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityCategory
from custom_components import DOMAIN, HonCoordinator
from custom_components.hon import HonEntity

NUMBERS: dict[str, tuple[NumberEntityDescription, ...]] = {
    "WM": (
        NumberEntityDescription(
            key="delayStatus",
            name="delayStatus",
            entity_category=EntityCategory.CONFIG
        ),
        NumberEntityDescription(
            key="delayTime",
            name="delayTime",
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG
        ),
        NumberEntityDescription(
            key="haier_SoakPrewashSelection",
            name="haier_SoakPrewashSelection",
            entity_category=EntityCategory.CONFIG
        ),
        NumberEntityDescription(
            key="rinseIterations",
            name="rinseIterations",
            entity_category=EntityCategory.CONFIG
        ),
        NumberEntityDescription(
            key="mainWashTime",
            name="mainWashTime",
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG
        ),
    ),
}


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    hon: HonConnection = hass.data[DOMAIN][entry.unique_id]
    coordinators = hass.data[DOMAIN]["coordinators"]
    appliances = []
    for device in hon.devices:
        if device.mac_address in coordinators:
            coordinator = hass.data[DOMAIN]["coordinators"][device.mac_address]
        else:
            coordinator = HonCoordinator(hass, device)
            hass.data[DOMAIN]["coordinators"][device.mac_address] = coordinator
        await coordinator.async_config_entry_first_refresh()

        if descriptions := NUMBERS.get(device.appliance_type_name):
            for description in descriptions:
                appliances.extend([
                    HonNumberEntity(hass, coordinator, entry, device, description)]
                )

    async_add_entities(appliances)


class HonNumberEntity(HonEntity, NumberEntity):
    def __init__(self, hass, coordinator, entry, device, description) -> None:
        super().__init__(hass, entry, coordinator, device)

        self._coordinator = coordinator
        self._data = device.settings[description.key]
        self.entity_description = description
        self._attr_unique_id = f"{super().unique_id}{description.key}"

        if isinstance(self._data, HonParameterRange):
            self._attr_native_max_value = self._data.max
            self._attr_native_min_value = self._data.min
            self._attr_native_step = self._data.step

    @property
    def native_value(self) -> float | None:
        return self._data.value

    async def async_set_native_value(self, value: float) -> None:
        self._data.value = value
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self):
        self._data = self._device.settings[self.entity_description.key]
        if isinstance(self._data, HonParameterRange):
            self._attr_native_max_value = self._data.max
            self._attr_native_min_value = self._data.min
            self._attr_native_step = self._data.step
        self._attr_native_value = self._data.value
        self.async_write_ha_state()