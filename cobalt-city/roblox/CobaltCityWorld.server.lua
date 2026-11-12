-- COBALT CITY RP — SAFE WORLD GENERATOR
-- Place as ServerScriptService/CobaltCityWorld
-- Owns ONLY Workspace.CobaltCityWorld. Moscow folders are never touched.

local Workspace = game:GetService("Workspace")
local ServerStorage = game:GetService("ServerStorage")
local HttpService = game:GetService("HttpService")

local CFG = {
    WORLD_NAME = "CobaltCityWorld",
    DATA_FOLDER = "CobaltCityData",
    ORIGIN = Vector3.new(50000, 0, 50000),
    CLEAR_OWN_WORLD = true,
    BATCH_SIZE = 100,
}

local function createWorld()
    local world = Workspace:FindFirstChild(CFG.WORLD_NAME)
    if world and not world:IsA("Folder") then
        error("Workspace.CobaltCityWorld exists but is not a Folder. Rename it manually; nothing was deleted.")
    end
    if not world then
        world = Instance.new("Folder")
        world.Name = CFG.WORLD_NAME
        world.Parent = Workspace
    elseif CFG.CLEAR_OWN_WORLD then
        world:ClearAllChildren()
    end
    return world
end

local function folder(parent, name)
    local f = Instance.new("Folder")
    f.Name = name
    f.Parent = parent
    return f
end

local function widthFor(tags)
    local widths = {motorway=22,trunk=19,primary=16,secondary=13,tertiary=11,
        residential=9,living_street=7,service=6,unclassified=9,track=5}
    local width = widths[tostring(tags.highway or "")] or 8
    local raw = tags.width and tonumber(string.match(tostring(tags.width), "[%d%.]+"))
    if raw then width = math.clamp(raw * 0.5, 4, 28) end
    return width
end

local function vec(p)
    return Vector3.new(p[1], 0, p[2]) + CFG.ORIGIN
end

local function addRoad(parent, a, b, width, name)
    local d = b-a
    if d.Magnitude < 0.5 then return end
    local part = Instance.new("Part")
    part.Name = name
    part.Anchored = true
    part.Material = Enum.Material.Asphalt
    part.Color = Color3.fromRGB(48,49,52)
    part.Size = Vector3.new(width,0.35,d.Magnitude)
    part.CFrame = CFrame.lookAt((a+b)*0.5,b)
    part.Parent = parent
end

local function addBuildingWalls(parent, ring, tags, index)
    local height = tonumber(tags.height)
    if height then height = math.clamp(height*0.5,3,220)
    else
        local levels = tonumber(tags["building:levels"])
        height = levels and math.clamp(levels*3.2,3,180) or 9
    end
    for i=1,#ring-1 do
        local a,b=vec(ring[i]),vec(ring[i+1])
        local d=b-a
        if d.Magnitude>0.5 then
            local wall=Instance.new("Part")
            wall.Name="Wall_"..index.."_"..i
            wall.Anchored=true
            wall.Material=Enum.Material.Concrete
            wall.Color=Color3.fromRGB(150,151,148)
            wall.Size=Vector3.new(0.7,height,d.Magnitude)
            wall.CFrame=CFrame.lookAt((a+b)*0.5+Vector3.new(0,height/2,0),b)
            wall.Parent=parent
        end
    end
end

local function main()
    local data=ServerStorage:FindFirstChild(CFG.DATA_FOLDER)
    if not data then error("Create ServerStorage/CobaltCityData and put exported chunk ModuleScripts inside.") end
    local world=createWorld()
    local modules=data:GetChildren()
    table.sort(modules,function(a,b) return a.Name<b.Name end)
    local processed=0
    for _,module in ipairs(modules) do
        if module:IsA("ModuleScript") and string.match(module.Name,"^CobaltChunk_") then
            local ok,raw=pcall(require,module)
            if not ok or type(raw)~="string" then
                warn("Bad chunk module: "..module.Name)
                continue
            end
            local decodedOk,payload=pcall(function() return HttpService:JSONDecode(raw) end)
            if not decodedOk or type(payload.features)~="table" then
                warn("Invalid chunk JSON: "..module.Name)
                continue
            end
            local chunk=folder(world,module.Name)
            local roads=folder(chunk,"Roads")
            local buildings=folder(chunk,"Buildings")
            local n=0
            for _,feature in ipairs(payload.features) do
                local tags=feature.properties or {}
                local geom=feature.geometry or {}
                if geom.type=="LineString" and tags.highway then
                    local c=geom.coordinates
                    for i=1,#c-1 do
                        addRoad(roads,vec(c[i]),vec(c[i+1]),widthFor(tags),"Road_"..n)
                        n+=1
                    end
                elseif geom.type=="Polygon" and tags.building and geom.coordinates[1] then
                    addBuildingWalls(buildings,geom.coordinates[1],tags,n)
                    n+=1
                end
                processed+=1
                if processed%CFG.BATCH_SIZE==0 then task.wait() end
            end
            print("[CobaltCity] "..module.Name.." loaded")
        end
    end
    print("[CobaltCity] Done. Features: "..processed.."; origin: "..tostring(CFG.ORIGIN))
    print("[CobaltCity] Moscow map folders were not modified.")
end

main()
