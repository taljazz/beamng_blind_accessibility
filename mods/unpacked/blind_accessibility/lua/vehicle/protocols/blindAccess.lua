-- BeamNG Blind Accessibility Protocol
-- Custom UDP protocol for sending accessibility data to external helper app
-- Protocol: BNBA (BeamNG Blind Accessibility)

local M = {}
M.type = "protocol"

-- Configuration
local config = {
    enabled = true,
    ip = "127.0.0.1",
    port = 4445,
    updateRate = 10, -- Hz for vehicle telemetry updates
}

-- Protocol constants
local HEADER = "BNBA"
local MSG_TYPE = {
    MENU = 0x01,      -- Menu navigation events
    VEHICLE = 0x02,   -- Vehicle telemetry
    ALERT = 0x03,     -- Important alerts/notifications
    DIALOG = 0x04,    -- Dialog boxes
    STATUS = 0x05,    -- Status updates (loading, etc.)
}

-- UDP socket reference
local udpSocket = nil
local lastUpdateTime = 0
local updateInterval = 1 / config.updateRate

-- Initialize the protocol
local function init()
    if not config.enabled then return end

    -- Create UDP socket using BeamNG's socket API
    udpSocket = socket.udp()
    if udpSocket then
        udpSocket:settimeout(0) -- Non-blocking
        log('I', 'blindAccess', 'Blind Accessibility Protocol initialized on port ' .. config.port)
    else
        log('E', 'blindAccess', 'Failed to create UDP socket')
    end
end

-- Build packet with header
local function buildPacket(msgType, payload)
    -- Packet structure:
    -- Header: "BNBA" (4 bytes)
    -- Type: 1 byte
    -- Length: 2 bytes (big-endian)
    -- Payload: UTF-8 string

    local payloadBytes = payload or ""
    local length = #payloadBytes

    -- Pack: header (4 chars) + type (1 byte) + length (2 bytes big-endian) + payload
    local packet = HEADER
        .. string.char(msgType)
        .. string.char(math.floor(length / 256))
        .. string.char(length % 256)
        .. payloadBytes

    return packet
end

-- Send a packet to the helper app
local function sendPacket(msgType, payload)
    if not udpSocket or not config.enabled then return false end

    local packet = buildPacket(msgType, payload)
    local success, err = udpSocket:sendto(packet, config.ip, config.port)

    if not success then
        log('W', 'blindAccess', 'Failed to send packet: ' .. tostring(err))
        return false
    end

    return true
end

-- Public API: Send menu event
local function sendMenuEvent(menuText, itemIndex, totalItems)
    local payload = string.format("%s|%d|%d", menuText or "", itemIndex or 0, totalItems or 0)
    return sendPacket(MSG_TYPE.MENU, payload)
end

-- Public API: Send alert
local function sendAlert(alertText, priority)
    local payload = string.format("%s|%d", alertText or "", priority or 1)
    return sendPacket(MSG_TYPE.ALERT, payload)
end

-- Public API: Send dialog
local function sendDialog(title, content, options)
    local optionsStr = table.concat(options or {}, ",")
    local payload = string.format("%s|%s|%s", title or "", content or "", optionsStr)
    return sendPacket(MSG_TYPE.DIALOG, payload)
end

-- Public API: Send status
local function sendStatus(statusText)
    return sendPacket(MSG_TYPE.STATUS, statusText or "")
end

-- Public API: Send vehicle telemetry
local function sendVehicleTelemetry(data)
    -- data = {speed, rpm, gear, steering, surface, etc.}
    local payload = string.format(
        "%.1f|%d|%s|%.2f|%s",
        data.speed or 0,
        data.rpm or 0,
        data.gear or "N",
        data.steering or 0,
        data.surface or "unknown"
    )
    return sendPacket(MSG_TYPE.VEHICLE, payload)
end

-- Called every graphics frame (for vehicle telemetry)
local function updateGFX(dt)
    if not config.enabled or not udpSocket then return end

    -- Rate limit telemetry updates
    lastUpdateTime = lastUpdateTime + dt
    if lastUpdateTime < updateInterval then return end
    lastUpdateTime = 0

    -- Gather vehicle telemetry from electrics
    local speed = electrics.values.wheelspeed or 0
    local rpm = electrics.values.rpm or 0
    local gear = electrics.values.gear_M or electrics.values.gear_A or 0
    local steering = electrics.values.steering_input or 0

    -- Convert speed from m/s to km/h
    local speedKmh = speed * 3.6

    -- Determine gear string
    local gearStr = "N"
    if gear > 0 then
        gearStr = tostring(gear)
    elseif gear < 0 then
        gearStr = "R"
    end

    -- Send telemetry
    sendVehicleTelemetry({
        speed = speedKmh,
        rpm = rpm,
        gear = gearStr,
        steering = steering,
        surface = "road" -- TODO: detect actual surface
    })
end

-- Cleanup
local function onExtensionUnloaded()
    if udpSocket then
        udpSocket:close()
        udpSocket = nil
    end
    log('I', 'blindAccess', 'Blind Accessibility Protocol unloaded')
end

-- Configuration update
local function setConfig(newConfig)
    for k, v in pairs(newConfig) do
        if config[k] ~= nil then
            config[k] = v
        end
    end

    -- Reinitialize if needed
    if udpSocket then
        udpSocket:close()
        udpSocket = nil
    end
    init()
end

local function getConfig()
    return config
end

-- Export public API
M.init = init
M.updateGFX = updateGFX
M.onExtensionUnloaded = onExtensionUnloaded

-- Public functions for external use
M.sendMenuEvent = sendMenuEvent
M.sendAlert = sendAlert
M.sendDialog = sendDialog
M.sendStatus = sendStatus
M.sendVehicleTelemetry = sendVehicleTelemetry
M.setConfig = setConfig
M.getConfig = getConfig

return M
