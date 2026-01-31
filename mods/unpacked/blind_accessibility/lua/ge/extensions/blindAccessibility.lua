-- BeamNG Blind Accessibility - Game Engine Extension
-- Handles menu navigation, UI events, and AI state announcements via UDP

local M = {}
M.dependencies = {}

-- Configuration
local config = {
    enabled = true,
    ip = "127.0.0.1",
    port = 4445,
    announcePosition = true,
    verbosity = "normal", -- "minimal", "normal", "verbose"
}

-- Protocol constants
local HEADER = "BNBA"
local MSG_TYPE = {
    MENU = 0x01,
    VEHICLE = 0x02,
    ALERT = 0x03,
    DIALOG = 0x04,
    STATUS = 0x05,
}

-- State tracking
local udpSocket = nil
local currentMenu = ""
local currentMenuItems = {}
local currentMenuIndex = 0
local lastAnnouncedText = ""

-- AI State tracking
local aiState = {
    vehicleModes = {},  -- Track AI mode per vehicle ID
    trafficActive = false,
    lastTrafficCount = 0,
    lastPolledModes = {},  -- For polling fallback
}

-- Traffic check timing
local trafficCheckInterval = 1.0
local trafficCheckTimer = 0

-- AI polling fallback (in case hooks don't fire)
local aiPollInterval = 0.5
local aiPollTimer = 0
local debugAiPolling = true  -- Set to true for debugging
local debugPollCount = 0     -- Count polls for debug output

-- AI Speed control
local aiCurrentSpeed = 20    -- Current AI speed in m/s (default ~72 km/h)
local aiSpeedStep = 2.78     -- Speed change step (~10 km/h)
local aiMinSpeed = 5.56      -- Minimum speed (~20 km/h)
local aiMaxSpeed = 55.56     -- Maximum speed (~200 km/h)

-- Initialize UDP socket
local function initSocket()
    if udpSocket then
        udpSocket:close()
        udpSocket = nil
    end

    udpSocket = socket.udp()
    if udpSocket then
        udpSocket:settimeout(0)
        log('I', 'blindAccessibility', 'UDP socket initialized for blind accessibility')
        return true
    else
        log('E', 'blindAccessibility', 'Failed to create UDP socket')
        return false
    end
end

-- Build and send packet
local function sendPacket(msgType, payload)
    if not udpSocket or not config.enabled then return false end

    local payloadBytes = payload or ""
    local length = #payloadBytes

    local packet = HEADER
        .. string.char(msgType)
        .. string.char(math.floor(length / 256))
        .. string.char(length % 256)
        .. payloadBytes

    local success, err = udpSocket:sendto(packet, config.ip, config.port)
    if not success then
        log('W', 'blindAccessibility', 'UDP send failed: ' .. tostring(err))
        return false
    end
    return true
end

-- Announce text (with deduplication)
local function announce(text, force)
    if not text or text == "" then return end
    if not force and text == lastAnnouncedText then return end

    lastAnnouncedText = text
    sendPacket(MSG_TYPE.MENU, text)
    log('D', 'blindAccessibility', 'Announced: ' .. text)
end

-- Announce menu item with position
local function announceMenuItem(itemText, index, total)
    if not itemText then return end

    local announcement = itemText
    if config.announcePosition and total > 0 then
        announcement = string.format("%s, %d of %d", itemText, index, total)
    end

    announce(announcement)
end

-- Announce alert (always speaks, interrupts)
local function announceAlert(text, priority)
    if not text or text == "" then return end

    local payload = string.format("%s|%d", text, priority or 1)
    sendPacket(MSG_TYPE.ALERT, payload)
    lastAnnouncedText = "" -- Allow re-announcement
    log('D', 'blindAccessibility', 'Alert: ' .. text)
end

-- Announce status change
local function announceStatus(text)
    if not text or text == "" then return end
    sendPacket(MSG_TYPE.STATUS, text)
    log('D', 'blindAccessibility', 'Status: ' .. text)
end

-- Announce dialog
local function announceDialog(title, content, options)
    if not title then return end

    local optionsStr = ""
    if options and #options > 0 then
        optionsStr = table.concat(options, ", ")
    end

    local payload = string.format("%s|%s|%s", title, content or "", optionsStr)
    sendPacket(MSG_TYPE.DIALOG, payload)
    log('D', 'blindAccessibility', 'Dialog: ' .. title)
end

-- =============================================================================
-- AI STATE MONITORING - Uses BeamNG's built-in hooks
-- =============================================================================

-- Get friendly name for AI mode
local function getAiModeName(mode)
    local modeNames = {
        disabled = "disabled",
        traffic = "traffic mode",
        random = "random exploration",
        span = "full map exploration",
        chase = "chase mode",
        flee = "flee mode",
        manual = "waypoint mode",
        follow = "follow mode",
        stopping = "stopping",
        script = "scripted path",
    }
    return modeNames[mode] or mode
end

-- Check if vehicle is the player's vehicle
local function isPlayerVehicle(vehicleId)
    local playerVid = be:getPlayerVehicleID(0)
    return playerVid and playerVid == vehicleId
end

-- Handle AI mode change (called by hook or polling)
local function handleAiModeChange(vehicleId, newAiMode, source)
    local oldMode = aiState.vehicleModes[vehicleId] or "disabled"

    -- Normalize modes for comparison
    local normalizedNew = (newAiMode == nil or newAiMode == "") and "disabled" or newAiMode
    local normalizedOld = (oldMode == nil or oldMode == "") and "disabled" or oldMode

    -- Skip if no actual change
    if normalizedNew == normalizedOld then return end

    log('I', 'blindAccessibility', 'AI mode change (' .. source .. '): vehicle ' .. tostring(vehicleId) .. ' ' .. normalizedOld .. ' -> ' .. normalizedNew)
    aiState.vehicleModes[vehicleId] = newAiMode

    -- Only announce for player vehicle
    if isPlayerVehicle(vehicleId) then
        if normalizedNew == "disabled" then
            announceAlert("AI disabled, manual control", 1)
        else
            announceAlert("AI enabled, " .. getAiModeName(newAiMode), 1)
        end
    else
        -- Non-player vehicle AI changed (could be traffic, chase vehicle, etc.)
        if config.verbosity == "verbose" then
            local vehicle = be:getObjectByID(vehicleId)
            local vehicleName = vehicle and vehicle:getJBeamFilename() or "Vehicle"
            if normalizedNew ~= "disabled" then
                announceStatus(vehicleName .. " AI: " .. getAiModeName(newAiMode))
            end
        end
    end
end

-- Called by BeamNG when any vehicle's AI mode changes
-- This is a built-in extension hook
local function onAiModeChange(vehicleId, newAiMode)
    log('I', 'blindAccessibility', 'onAiModeChange HOOK FIRED: vehicle ' .. tostring(vehicleId) .. ' -> ' .. tostring(newAiMode))
    handleAiModeChange(vehicleId, newAiMode, "hook")
end

-- Polling fallback: Check AI state for player vehicle
local function pollAiState()
    local playerVid = be:getPlayerVehicleID(0)
    if not playerVid or playerVid < 0 then return end

    local vehicle = be:getObjectByID(playerVid)
    if not vehicle then return end

    -- Request AI mode from vehicle Lua - comprehensive check
    local cmd = string.format([[
        local mode = "disabled"
        local debugInfo = "ai="..tostring(ai)

        if ai then
            -- Try all known ways to get AI mode
            if ai.mode and ai.mode ~= "" then
                mode = ai.mode
                debugInfo = debugInfo .. " mode=" .. tostring(ai.mode)
            end
            if ai.driveInLaneFlag ~= nil then
                debugInfo = debugInfo .. " inLane=" .. tostring(ai.driveInLaneFlag)
            end
            -- Check if AI is actually controlling the vehicle
            if ai.stateChanged ~= nil then
                debugInfo = debugInfo .. " stateChanged=" .. tostring(ai.stateChanged)
            end
        end

        -- Also check electrics for AI control indicator
        if electrics and electrics.values then
            local aiVal = electrics.values.ai
            local aiCtrl = electrics.values.aiControlled
            if aiVal ~= nil then
                debugInfo = debugInfo .. " elec.ai=" .. tostring(aiVal)
                if aiVal == 1 or aiVal == true then
                    if mode == "disabled" then mode = "enabled" end
                end
            end
            if aiCtrl ~= nil then
                debugInfo = debugInfo .. " elec.aiControlled=" .. tostring(aiCtrl)
            end
        end

        -- Check controller inputs
        if controller then
            local mainCtrl = controller.mainController
            if mainCtrl then
                debugInfo = debugInfo .. " mainCtrl=" .. tostring(mainCtrl)
            end
        end

        obj:queueGameEngineLua("extensions.blindAccessibility.onAiModePolled(%d, '" .. tostring(mode) .. "', [[" .. debugInfo .. "]])")
    ]], playerVid)
    vehicle:queueLuaCommand(cmd)
end

-- Called when polling receives AI mode response
local function onAiModePolled(vehicleId, mode, debugInfo)
    debugPollCount = debugPollCount + 1

    if debugAiPolling then
        log('I', 'blindAccessibility', 'AI poll: vid=' .. tostring(vehicleId) .. ' mode=' .. tostring(mode) .. ' debug=[' .. tostring(debugInfo or "") .. ']')

        -- Send debug status via UDP every 10 polls (5 seconds) so user can see it in helper
        if debugPollCount == 10 then
            announceStatus("AI polling active, mode=" .. tostring(mode))
        end
    end

    local lastPolled = aiState.lastPolledModes[vehicleId]
    if lastPolled ~= mode then
        log('I', 'blindAccessibility', 'AI mode change detected via polling: ' .. tostring(lastPolled) .. ' -> ' .. tostring(mode))
        aiState.lastPolledModes[vehicleId] = mode
        -- Only use polling result if we haven't seen this change via hook
        if aiState.vehicleModes[vehicleId] ~= mode then
            handleAiModeChange(vehicleId, mode, "poll")
        end
    end
end

-- Check traffic state (still needs polling as there's no direct hook)
local function checkTrafficState()
    local trafficCount = 0

    -- Try to count traffic vehicles using gameplay_traffic
    if gameplay_traffic then
        local success, count = pcall(function()
            if gameplay_traffic.getNumOfTraffic then
                return gameplay_traffic.getNumOfTraffic()
            elseif gameplay_traffic.getTrafficList then
                local list = gameplay_traffic.getTrafficList()
                return list and #list or 0
            end
            return 0
        end)
        if success and count then
            trafficCount = count
        end
    end

    -- Detect traffic spawning/clearing
    if trafficCount > 0 and aiState.lastTrafficCount == 0 then
        aiState.trafficActive = true
        announceAlert("Traffic spawned, " .. trafficCount .. " vehicles", 1)
    elseif trafficCount == 0 and aiState.lastTrafficCount > 0 then
        aiState.trafficActive = false
        announceAlert("Traffic cleared", 1)
    end

    aiState.lastTrafficCount = trafficCount
end

-- Called when traffic system starts
local function onTrafficStarted()
    log('I', 'blindAccessibility', 'Traffic system started')
    -- Will be picked up by the next traffic check
end

-- =============================================================================
-- MENU EVENT HANDLERS
-- =============================================================================

-- Handle menu state change from UI
local function onMenuStateChanged(data)
    if not data then return end

    local menuName = data.menuName or ""
    local items = data.items or {}
    local selectedIndex = data.selectedIndex or 1
    local selectedText = data.selectedText or ""

    currentMenu = menuName
    currentMenuItems = items
    currentMenuIndex = selectedIndex

    if config.verbosity == "verbose" then
        if menuName ~= "" then
            announce("Menu: " .. menuName, true)
        end
    end

    announceMenuItem(selectedText, selectedIndex, #items)
end

-- Handle menu item focus change
local function onMenuItemFocused(data)
    if not data then return end

    local itemText = data.text or data.label or ""
    local index = data.index or 0
    local total = data.total or #currentMenuItems

    currentMenuIndex = index
    announceMenuItem(itemText, index, total)
end

-- Handle menu opened
local function onMenuOpened(data)
    if not data then return end

    local menuName = data.name or data.menuName or "Menu"
    currentMenu = menuName

    if config.verbosity ~= "minimal" then
        announce(menuName .. " opened", true)
    end
end

-- Handle menu closed
local function onMenuClosed(data)
    if config.verbosity == "verbose" then
        announce("Menu closed", true)
    end
    currentMenu = ""
    currentMenuItems = {}
    currentMenuIndex = 0
end

-- Handle button/action activation
local function onActionActivated(data)
    if not data then return end

    local actionName = data.name or data.action or ""
    if actionName ~= "" and config.verbosity == "verbose" then
        announce("Activated: " .. actionName)
    end
end

-- Handle loading state
local function onLoadingStateChanged(data)
    if not data then return end

    if data.loading then
        announceStatus("Loading " .. (data.what or ""))
    else
        announceStatus("Loading complete")
    end
end

-- Handle vehicle spawn
local function onVehicleSpawned(vehicleId)
    local vehicle = be:getObjectByID(vehicleId)
    if vehicle then
        local vehicleName = vehicle:getJBeamFilename() or "Vehicle"
        announceAlert("Vehicle spawned: " .. vehicleName, 1)
    end
end

-- Handle level loaded
local function onClientStartMission(levelPath)
    local levelName = levelPath or "Level"
    levelName = levelName:match("([^/]+)$") or levelName
    announceAlert("Level loaded: " .. levelName, 1)

    -- Reset AI state tracking
    aiState.vehicleModes = {}
    aiState.trafficActive = false
    aiState.lastTrafficCount = 0
end

-- =============================================================================
-- ACCESSIBILITY EVENT ROUTER
-- =============================================================================

-- Called from UI app with accessibility data
local function onAccessibilityEvent(data)
    if not data or not data.type then return end

    local eventType = data.type

    if eventType == "menuState" then
        onMenuStateChanged(data)
    elseif eventType == "menuItemFocused" then
        onMenuItemFocused(data)
    elseif eventType == "menuOpened" then
        onMenuOpened(data)
    elseif eventType == "menuClosed" then
        onMenuClosed(data)
    elseif eventType == "actionActivated" then
        onActionActivated(data)
    elseif eventType == "alert" then
        announceAlert(data.text, data.priority)
    elseif eventType == "dialog" then
        announceDialog(data.title, data.content, data.options)
    elseif eventType == "status" then
        announceStatus(data.text)
    elseif eventType == "custom" then
        announce(data.text, data.force)
    end
end

-- =============================================================================
-- AI SPEED CONTROL
-- =============================================================================

-- Apply current speed to AI
local function applyAiSpeed()
    local playerVid = be:getPlayerVehicleID(0)
    if not playerVid or playerVid < 0 then return false end

    local vehicle = be:getObjectByID(playerVid)
    if not vehicle then return false end

    -- Set the AI speed using "set" mode to maintain exact speed
    local cmd = string.format('ai.setSpeed(%f, "set")', aiCurrentSpeed)
    vehicle:queueLuaCommand(cmd)
    return true
end

-- Convert m/s to km/h for announcement
local function msToKmh(ms)
    return math.floor(ms * 3.6 + 0.5)
end

-- Increase AI speed
local function aiSpeedUp()
    local newSpeed = aiCurrentSpeed + aiSpeedStep
    if newSpeed > aiMaxSpeed then
        newSpeed = aiMaxSpeed
        announceAlert("Maximum speed, " .. msToKmh(newSpeed) .. " kilometers per hour", 1)
    else
        aiCurrentSpeed = newSpeed
        if applyAiSpeed() then
            announceAlert("Speed " .. msToKmh(aiCurrentSpeed) .. " kilometers per hour", 1)
        else
            announceAlert("No vehicle for AI speed", 1)
        end
    end
end

-- Decrease AI speed
local function aiSpeedDown()
    local newSpeed = aiCurrentSpeed - aiSpeedStep
    if newSpeed < aiMinSpeed then
        newSpeed = aiMinSpeed
        announceAlert("Minimum speed, " .. msToKmh(newSpeed) .. " kilometers per hour", 1)
    else
        aiCurrentSpeed = newSpeed
        if applyAiSpeed() then
            announceAlert("Speed " .. msToKmh(aiCurrentSpeed) .. " kilometers per hour", 1)
        else
            announceAlert("No vehicle for AI speed", 1)
        end
    end
end

-- Announce current AI speed
local function aiAnnounceSpeed()
    announceAlert("AI speed " .. msToKmh(aiCurrentSpeed) .. " kilometers per hour", 1)
end

-- =============================================================================
-- EXTENSION LIFECYCLE
-- =============================================================================

local function onExtensionLoaded()
    log('I', 'blindAccessibility', 'Blind Accessibility extension loading...')
    log('I', 'blindAccessibility', 'AI hooks registered: onAiModeChange, onTrafficStarted')

    if not initSocket() then
        log('E', 'blindAccessibility', 'Failed to initialize, extension disabled')
        config.enabled = false
        return
    end

    -- Input actions are defined in JSON file:
    -- lua/ge/extensions/core/input/actions/blindAccessibility.json
    -- Default keybindings are in:
    -- settings/inputmaps/keyboard_blindAccessibility.json
    log('I', 'blindAccessibility', 'Input actions loaded from JSON files')

    announceStatus("Blind Accessibility mod loaded")
    log('I', 'blindAccessibility', 'Blind Accessibility extension loaded successfully')
    log('I', 'blindAccessibility', 'AI polling fallback active (interval: ' .. aiPollInterval .. 's)')
end

local function onExtensionUnloaded()
    if udpSocket then
        udpSocket:close()
        udpSocket = nil
    end
    log('I', 'blindAccessibility', 'Blind Accessibility extension unloaded')
end

-- Alternative: Check AI state from GE side using electrics
local function pollAiStateGE()
    local playerVid = be:getPlayerVehicleID(0)
    if not playerVid or playerVid < 0 then return end

    -- Try to get AI state via core_vehicle_manager if available
    if core_vehicle_manager then
        local vehData = core_vehicle_manager.getVehicleData(playerVid)
        if vehData and vehData.ai then
            local mode = vehData.ai.mode or "disabled"
            if debugAiPolling then
                log('D', 'blindAccessibility', 'GE poll: AI mode from vehicle data = ' .. tostring(mode))
            end
            local lastMode = aiState.lastPolledModes[playerVid]
            if lastMode ~= mode then
                aiState.lastPolledModes[playerVid] = mode
                if aiState.vehicleModes[playerVid] ~= mode then
                    handleAiModeChange(playerVid, mode, "ge-poll")
                end
            end
        end
    end
end

-- Called every frame - monitors traffic and AI state
local function onUpdate(dtReal, dtSim, dtRaw)
    -- Traffic monitoring
    trafficCheckTimer = trafficCheckTimer + dtReal
    if trafficCheckTimer >= trafficCheckInterval then
        trafficCheckTimer = 0
        checkTrafficState()
    end

    -- AI state polling fallback (in case hooks don't fire)
    aiPollTimer = aiPollTimer + dtReal
    if aiPollTimer >= aiPollInterval then
        aiPollTimer = 0

        local playerVid = be:getPlayerVehicleID(0)
        if playerVid and playerVid >= 0 then
            if debugAiPolling then
                log('D', 'blindAccessibility', 'Polling AI state for vehicle ' .. tostring(playerVid))
            end

            -- Simple connectivity test first
            local vehicle = be:getObjectByID(playerVid)
            if vehicle then
                -- Simple ping to verify communication works
                vehicle:queueLuaCommand('obj:queueGameEngineLua("extensions.blindAccessibility.onAiPollPing()")')
                -- Then do full AI check
                pollAiState()
            end

            pollAiStateGE()    -- GE side method
        end
    end
end

-- =============================================================================
-- CONFIGURATION
-- =============================================================================

local function setConfig(newConfig)
    for k, v in pairs(newConfig) do
        if config[k] ~= nil then
            config[k] = v
        end
    end
    initSocket()
end

local function getConfig()
    return config
end

local function isEnabled()
    return config.enabled
end

local function setEnabled(enabled)
    config.enabled = enabled
    if enabled then
        initSocket()
        announceStatus("Blind Accessibility enabled")
    else
        announceStatus("Blind Accessibility disabled")
    end
end

-- =============================================================================
-- PUBLIC API
-- =============================================================================

-- Export public API
M.onExtensionLoaded = onExtensionLoaded
M.onExtensionUnloaded = onExtensionUnloaded
M.onUpdate = onUpdate

-- BeamNG built-in hooks
M.onAiModeChange = onAiModeChange        -- Called when any vehicle's AI mode changes
M.onTrafficStarted = onTrafficStarted    -- Called when traffic system starts
M.onVehicleSpawned = onVehicleSpawned
M.onClientStartMission = onClientStartMission

-- Polling callback (for fallback AI detection)
M.onAiModePolled = onAiModePolled

-- Simple ping callback to verify GE-vehicle communication
local pingReceived = false
local function onAiPollPing()
    if not pingReceived then
        pingReceived = true
        log('I', 'blindAccessibility', 'Vehicle-to-GE communication verified!')
        announceStatus("AI monitoring active")
    end
end
M.onAiPollPing = onAiPollPing

-- Public API for UI app and other extensions
M.onAccessibilityEvent = onAccessibilityEvent
M.announce = announce
M.announceAlert = announceAlert
M.announceStatus = announceStatus
M.announceDialog = announceDialog
M.announceMenuItem = announceMenuItem

-- Configuration
M.setConfig = setConfig
M.getConfig = getConfig
M.isEnabled = isEnabled
M.setEnabled = setEnabled

-- AI Speed control (for keybinds and console)
M.aiSpeedUp = aiSpeedUp
M.aiSpeedDown = aiSpeedDown
M.aiAnnounceSpeed = aiAnnounceSpeed

return M
