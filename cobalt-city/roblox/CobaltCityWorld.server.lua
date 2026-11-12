-- COBALT CITY RP — STREAMED, SAFE WORLD LOADER
-- Put this Script in ServerScriptService as CobaltCityWorld.
-- It creates/clears ONLY Workspace.CobaltCityWorld. Moscow objects are untouched.

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local ServerStorage = game:GetService("ServerStorage")
local HttpService = game:GetService("HttpService")

local CFG = {
    WORLD_NAME = "CobaltCityWorld",
    DATA_FOLDER = "CobaltCityData",
    ORIGIN = Vector3.new(50000, 0, 50000),
    CHUNK_SIZE = 1024,
    LOAD_RADIUS = 1,
    UPDATE_SECONDS = 4,
    BATCH_SIZE = 120,
}

local function getWorld()
    local world = Workspace:FindFirstChild(CFG.WORLD_NAME)
    if world and not world:IsA("Folder") then
        error("Workspace.CobaltCityWorld exists but is not a Folder. Rename that object manually; nothing was deleted.")
    end
    if not world then
        world = Instance.new("Folder")
        world.Name = CFG.WORLD_NAME
        world.Parent = Workspace
    end
    return world
end

local function widthFor(tags)
    local widths = {
        motorway=22, motorway_link=14, trunk=19, trunk_link=13,
        primary=16, primary_link=12, secondary=13, secondary_link=10,
        tertiary=11, tertiary_link=9, residential=9,
        living_street=7, service=6, unclassified=8, track=5
    }
    local width = widths[tostring(tags.highway or "")] or 8
    local raw = tags.width and tonumber(string.match(tostring(tags.width), "[%d%.]+"))
    if raw then width = math.clamp(raw * 0.5, 4, 28) end
    return width
end

local function vec(p)
    return Vector3.new(p[1], 0, p[2]) + CFG.ORIGIN
end

local function addRoad(parent, a, b, width, index)
    local delta = b-a
    if delta.Magnitude < 1 then return end
    local part = Instance.new("Part")
    part.Name = "Road_" .. index
    part.Anchored = true
    part.CanTouch = false
    part.Material = Enum.Material.Asphalt
    part.Color = Color3.fromRGB(48, 49, 52)
    part.Size = Vector3.new(width, 0.35, delta.Magnitude)
    part.CFrame = CFrame.lookAt((a+b)*0.5, b)
    part.Parent = parent
end

local function addBuilding(parent, ring, tags, index)
    if #ring < 4 then return end
    local height = tonumber(tags.height)
    if height then
        height = math.clamp(height * 0.5, 3, 220)
    else
        local levels = tonumber(tags["building:levels"])
        height = levels and math.clamp(levels * 3.2, 3, 180) or 9
    end
    local model = Instance.new("Model")
    model.Name = "Building_" .. index
    model.Parent = parent
    for i=1,#ring-1 do
        local a,b = vec(ring[i]),vec(ring[i+1])
        local delta = b-a
        if delta.Magnitude > 1 then
            local wall = Instance.new("Part")
            wall.Name = "Wall_" .. i
            wall.Anchored = true
            wall.CanTouch = false
            wall.Material = Enum.Material.Concrete
            wall.Color = Color3.fromRGB(150,151,148)
            wall.Size = Vector3.new(0.7,height,delta.Magnitude)
            wall.CFrame = CFrame.lookAt((a+b)*0.5+Vector3.new(0,height/2,0),b)
            wall.Parent = model
        end
    end
end

local function parseChunkName(name)
    local x,z = string.match(name, "^CobaltChunk_(-?%d+)_(-?%d+)_Part_(%d+)$")
    if not x then return nil end
    return tonumber(x), tonumber(z)
end

local function getCharacterChunk(player)
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not root then return nil end
    local localPos = root.Position - CFG.ORIGIN
    return math.floor(localPos.X/CFG.CHUNK_SIZE), math.floor(localPos.Z/CFG.CHUNK_SIZE)
end

local function main()
    local data = ServerStorage:FindFirstChild(CFG.DATA_FOLDER)
    if not data then error("Create ServerStorage/CobaltCityData and add all exported CobaltChunk ModuleScripts.") end

    local world = getWorld()
    if not world:FindFirstChild("CobaltCitySpawn") then
        local spawn = Instance.new("SpawnLocation")
        spawn.Name = "CobaltCitySpawn"
        spawn.Size = Vector3.new(12, 1, 12)
        spawn.Position = CFG.ORIGIN + Vector3.new(0, 1, 0)
        spawn.Anchored = true
        spawn.Transparency = 1
        spawn.CanCollide = true
        spawn.Neutral = true
        spawn.Duration = 0
        spawn.Parent = world
    end

    local available = {}
    for _, module in ipairs(data:GetChildren()) do
        if module:IsA("ModuleScript") then
            local x,z = parseChunkName(module.Name)
            if x then
                local key = x .. ":" .. z
                available[key] = available[key] or {x=x,z=z,modules={}}
                table.insert(available[key].modules,module)
            end
        end
    end
    for _, entry in pairs(available) do
        table.sort(entry.modules,function(a,b) return a.Name < b.Name end)
    end

    local loaded = {}
    local busy = false

    local function loadChunk(key, entry)
        if loaded[key] then return end
        local chunk = Instance.new("Folder")
        chunk.Name = "CobaltChunk_" .. entry.x .. "_" .. entry.z
        chunk.Parent = world
        loaded[key] = chunk
        local roads = Instance.new("Folder"); roads.Name="Roads"; roads.Parent=chunk
        local buildings = Instance.new("Folder"); buildings.Name="Buildings"; buildings.Parent=chunk
        local roadIndex, buildingIndex, made = 0, 0, 0

        for _, module in ipairs(entry.modules) do
            local ok, raw = pcall(require,module)
            if not ok or type(raw) ~= "string" then
                warn("[CobaltCity] Cannot read " .. module.Name)
                continue
            end
            local decoded, payload = pcall(function() return HttpService:JSONDecode(raw) end)
            if not decoded or type(payload.features) ~= "table" then
                warn("[CobaltCity] Invalid JSON in " .. module.Name)
                continue
            end
            for _, feature in ipairs(payload.features) do
                local tags = feature.properties or {}
                local geom = feature.geometry or {}
                if geom.type == "LineString" and tags.highway then
                    local coords = geom.coordinates
                    for i=1,#coords-1 do
                        roadIndex += 1
                        addRoad(roads, vec(coords[i]), vec(coords[i+1]), widthFor(tags), roadIndex)
                        made += 1
                        if made % CFG.BATCH_SIZE == 0 then task.wait() end
                    end
                elseif geom.type == "Polygon" and tags.building and geom.coordinates[1] then
                    buildingIndex += 1
                    addBuilding(buildings, geom.coordinates[1], tags, buildingIndex)
                    made += #geom.coordinates[1]
                    if made % CFG.BATCH_SIZE < #geom.coordinates[1] then task.wait() end
                end
            end
        end
        print("[CobaltCity] Loaded " .. chunk.Name .. " (" .. #entry.modules .. " parts)")
    end

    local function updateChunks()
        if busy then return end
        busy = true
        local wanted = {}
        for _, player in ipairs(Players:GetPlayers()) do
            local cx,cz = getCharacterChunk(player)
            if cx then
                for dx=-CFG.LOAD_RADIUS,CFG.LOAD_RADIUS do
                    for dz=-CFG.LOAD_RADIUS,CFG.LOAD_RADIUS do
                        local key=(cx+dx) .. ":" .. (cz+dz)
                        if available[key] then wanted[key]=available[key] end
                    end
                end
            end
        end
        for key,entry in pairs(wanted) do
            loadChunk(key,entry)
        end
        for key,folder in pairs(loaded) do
            if not wanted[key] then
                folder:Destroy()
                loaded[key]=nil
                print("[CobaltCity] Unloaded " .. key)
            end
        end
        busy = false
    end

    print("[CobaltCity] Ready. Spatial chunks: " .. tostring(#data:GetChildren()) .. " module parts scanned.")
    print("[CobaltCity] World origin: " .. tostring(CFG.ORIGIN) .. ". Moscow map is untouched.")
    while true do
        updateChunks()
        task.wait(CFG.UPDATE_SECONDS)
    end
end

main()
