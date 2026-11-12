--========================================================
-- COBALT CITY RP — MOSCOW TEST MAP 0.3
-- IMPORTANT: This creates MoscowCityMap_Test only.
-- Your existing CobaltCityMap is NOT deleted or modified.
--
-- Put the generated ModuleScript "MoscowMapData" into ServerStorage.
-- Put this Script into ServerScriptService and press Play.
--========================================================

local Workspace = game:GetService("Workspace")
local Lighting = game:GetService("Lighting")
local ServerStorage = game:GetService("ServerStorage")
local Players = game:GetService("Players")

local dataModule = ServerStorage:WaitForChild("MoscowMapData", 30)
if not dataModule then
	error("MoscowMapData not found in ServerStorage. Import the generated ModuleScript first.")
end

local ok, DATA = pcall(require, dataModule)
if not ok or type(DATA) ~= "table" then
	error("MoscowMapData could not be loaded: " .. tostring(DATA))
end

----------------------------------------------------------
-- Cinematic lighting
----------------------------------------------------------
pcall(function()
	Lighting.Technology = Enum.Technology.Future
end)
Lighting.GlobalShadows = true
Lighting.Brightness = 2.1
Lighting.ClockTime = 17.1
Lighting.ExposureCompensation = 0.05
Lighting.EnvironmentDiffuseScale = 0.55
Lighting.EnvironmentSpecularScale = 0.75
Lighting.ShadowSoftness = 0.35
Lighting.Ambient = Color3.fromRGB(95, 100, 118)
Lighting.OutdoorAmbient = Color3.fromRGB(135, 135, 145)
Lighting.FogStart = 900
Lighting.FogEnd = 2600
Lighting.FogColor = Color3.fromRGB(190, 180, 170)

local function getEffect(className)
	local effect = Lighting:FindFirstChildOfClass(className)
	if not effect then
		effect = Instance.new(className)
		effect.Parent = Lighting
	end
	return effect
end

local atmosphere = getEffect("Atmosphere")
atmosphere.Density = 0.22
atmosphere.Offset = 0.1
atmosphere.Color = Color3.fromRGB(225, 215, 205)
atmosphere.Decay = Color3.fromRGB(105, 125, 155)
atmosphere.Glare = 0.12
atmosphere.Haze = 1.1

local color = getEffect("ColorCorrectionEffect")
color.Brightness = 0.015
color.Contrast = 0.12
color.Saturation = 0.08
color.TintColor = Color3.fromRGB(255, 242, 225)

local bloom = getEffect("BloomEffect")
bloom.Intensity = 0.12
bloom.Size = 20
bloom.Threshold = 1.3

----------------------------------------------------------
-- Create an isolated test folder. Do not touch old map.
----------------------------------------------------------
local previous = Workspace:FindFirstChild("MoscowCityMap_Test")
if previous then
	previous:Destroy()
end

local map = Instance.new("Folder")
map.Name = "MoscowCityMap_Test"
map.Parent = Workspace

local roadsFolder = Instance.new("Folder")
roadsFolder.Name = "Roads"
roadsFolder.Parent = map

local blocksFolder = Instance.new("Folder")
blocksFolder.Name = "Buildings"
blocksFolder.Parent = map

local natureFolder = Instance.new("Folder")
natureFolder.Name = "Parks and Water"
natureFolder.Parent = map

-- Keep the imported Moscow test map far away from the old synthetic map.
-- All OSM coordinates remain unchanged relative to each other.
local MAP_OFFSET = Vector3.new(12000, 0, 12000)

local function makePart(parent, name, size, cf, material, color, collide)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.CFrame = cf + MAP_OFFSET
	p.Anchored = true
	p.Material = material
	p.Color = color
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.CanCollide = collide ~= false
	p.CastShadow = true
	p.Parent = parent
	return p
end

local radius = tonumber(DATA.Radius) or 1400

-- A small clear zone at the center of the imported Moscow map.
-- Features inside this radius are omitted to make a safe city plaza.
local spawnX, spawnZ = 0, 0
local spawnClearRadius = 72

local function isInsideSpawnZone(x, z, extra)
	local dx = x - spawnX
	local dz = z - spawnZ
	return (dx * dx + dz * dz) < (spawnClearRadius + (extra or 0)) ^ 2
end
makePart(
	map,
	"Moscow Ground",
	Vector3.new(radius * 2 + 300, 5, radius * 2 + 300),
	CFrame.new(0, -2.5, 0),
	Enum.Material.Ground,
	Color3.fromRGB(93, 105, 83),
	true
)

----------------------------------------------------------
-- Water areas
----------------------------------------------------------
for i, item in ipairs(DATA.Water or {}) do
	local x, z, w, d = item[1], item[2], item[3], item[4]
	if w and d and not isInsideSpawnZone(x, z, math.max(w, d) * 0.5) then
		makePart(
			natureFolder, "Moscow Water " .. i,
			Vector3.new(w, 0.12, d),
			CFrame.new(x, 0.16, z),
			Enum.Material.Glass,
			Color3.fromRGB(55, 125, 165),
			false
		)
	end
	if i % 40 == 0 then task.wait() end
end

----------------------------------------------------------
-- Parks and green areas
----------------------------------------------------------
for i, item in ipairs(DATA.Parks or {}) do
	local x, z, w, d = item[1], item[2], item[3], item[4]
	if w and d and not isInsideSpawnZone(x, z, math.max(w, d) * 0.5) then
		makePart(
			natureFolder, "Green Area " .. i,
			Vector3.new(w, 0.12, d),
			CFrame.new(x, 0.08, z),
			Enum.Material.Grass,
			Color3.fromRGB(72, 112, 70),
			true
		)
	end
	if i % 50 == 0 then task.wait() end
end

----------------------------------------------------------
-- Real road layout from OSM centerline segments
----------------------------------------------------------
for i, item in ipairs(DATA.Roads or {}) do
	local x, z, width, length, angle = item[1], item[2], item[3], item[4], item[5]
	if width and length and length > 1 and not isInsideSpawnZone(x, z, length * 0.5) then
		makePart(
			roadsFolder, "Road Segment " .. i,
			Vector3.new(math.max(2, width), 0.22, math.max(2, length)),
			CFrame.new(x, 0.28, z) * CFrame.Angles(0, math.rad(angle or 0), 0),
			Enum.Material.Asphalt,
			Color3.fromRGB(42, 45, 49),
			true
		)
	end
	if i % 250 == 0 then task.wait() end
end

----------------------------------------------------------
-- Buildings: varied Moscow-style facades, not plain cubes
----------------------------------------------------------
local facadeColors = {
	Color3.fromRGB(190, 174, 148),
	Color3.fromRGB(165, 157, 145),
	Color3.fromRGB(205, 195, 174),
	Color3.fromRGB(145, 151, 158),
	Color3.fromRGB(177, 164, 151),
	Color3.fromRGB(125, 137, 145),
	Color3.fromRGB(205, 181, 151),
}
local glassColors = {
	Color3.fromRGB(72, 116, 139),
	Color3.fromRGB(91, 137, 155),
	Color3.fromRGB(105, 145, 160),
}
local rng = Random.new(240519)

-- Filter heavily overlapping building rectangles before creating parts.
-- This removes duplicate/stacked footprints from the simplified OSM export.
local acceptedFootprints = {}
local skippedOverlapping = 0

for i, item in ipairs(DATA.Buildings or {}) do
	local x, z, width, depth, height = item[1], item[2], item[3], item[4], item[5]
	if width and depth and height and not isInsideSpawnZone(x, z, math.max(width, depth) * 0.5) then
		width = math.max(5, math.min(width, 75))
		depth = math.max(5, math.min(depth, 75))
		height = math.max(8, math.min(height, 90))

		local overlapsTooMuch = false
		local area = width * depth
		for _, other in ipairs(acceptedFootprints) do
			local overlapX = math.max(0, math.min(x + width/2, other.x + other.w/2) - math.max(x - width/2, other.x - other.w/2))
			local overlapZ = math.max(0, math.min(z + depth/2, other.z + other.d/2) - math.max(z - depth/2, other.z - other.d/2))
			local overlapArea = overlapX * overlapZ
			local smallerArea = math.min(area, other.area)
			if smallerArea > 0 and overlapArea / smallerArea > 0.55 then
				overlapsTooMuch = true
				break
			end
		end

		if overlapsTooMuch then
			skippedOverlapping += 1
		else
			table.insert(acceptedFootprints, {
				x = x, z = z, w = width, d = depth, area = area
			})

		local facade = facadeColors[rng:NextInteger(1, #facadeColors)]
		local glass = glassColors[rng:NextInteger(1, #glassColors)]
		local model = Instance.new("Model")
		model.Name = "Moscow Building " .. i
		model.Parent = blocksFolder

		makePart(
			model, "Main Facade",
			Vector3.new(width, height, depth),
			CFrame.new(x, height / 2 + 0.15, z),
			Enum.Material.SmoothPlastic,
			facade,
			true
		)

		makePart(
			model, "Roof",
			Vector3.new(width + 1.2, 1.1, depth + 1.2),
			CFrame.new(x, height + 0.75, z),
			Enum.Material.Concrete,
			Color3.fromRGB(65, 68, 73),
			true
		)


		-- A restrained row of windows on two street-facing sides.
		local windowCount = math.clamp(math.floor(width / 8), 1, 5)
		local windowY = math.max(5, math.min(height - 4, height * 0.55))
		for w = 1, windowCount do
			local wx = x - width / 2 + (width / (windowCount + 1)) * w
			makePart(
				model, "Front Window",
				Vector3.new(math.max(2, width / (windowCount + 1) * 0.58), math.max(2.2, height * 0.12), 0.22),
				CFrame.new(wx, windowY, z - depth / 2 - 0.13),
				Enum.Material.Glass,
				glass,
				false
			)
		end

		local sideWindowCount = math.clamp(math.floor(depth / 10), 1, 3)
		for w = 1, sideWindowCount do
			local wz = z - depth / 2 + (depth / (sideWindowCount + 1)) * w
			makePart(
				model, "Side Window",
				Vector3.new(0.22, math.max(2.2, height * 0.12), math.max(2, depth / (sideWindowCount + 1) * 0.55)),
				CFrame.new(x + width / 2 + 0.13, windowY, wz),
				Enum.Material.Glass,
				glass,
				false
			)
		end

		-- Decorative cornice gives the roofline a finished silhouette.
		makePart(
			model, "Facade Cornice",
			Vector3.new(width + 1.4, 0.8, depth + 1.4),
			CFrame.new(x, height - 0.1, z),
			Enum.Material.Concrete,
			facade:Lerp(Color3.new(1,1,1), 0.16),
			false
		)
		end
	end

	if i % 40 == 0 then task.wait() end
end

----------------------------------------------------------
-- Moscow city plaza and player spawn
----------------------------------------------------------
local plaza = makePart(
	map,
	"Moscow Central Test Plaza",
	Vector3.new(150, 0.35, 150),
	CFrame.new(spawnX, 0.18, spawnZ),
	Enum.Material.Pavement,
	Color3.fromRGB(125, 127, 128),
	true
)

-- Decorative paving strips around the plaza.
for i = -2, 2 do
	makePart(map, "Plaza Paving X " .. i, Vector3.new(150, 0.08, 1.2),
		CFrame.new(spawnX, 0.4, spawnZ + i * 24), Enum.Material.Slate,
		Color3.fromRGB(92, 96, 100), false)
	makePart(map, "Plaza Paving Z " .. i, Vector3.new(1.2, 0.08, 150),
		CFrame.new(spawnX + i * 24, 0.4, spawnZ), Enum.Material.Slate,
		Color3.fromRGB(92, 96, 100), false)
end

-- Four street lamps around the square.
for i, offset in ipairs({
	Vector3.new(-58, 0, -58),
	Vector3.new(58, 0, -58),
	Vector3.new(-58, 0, 58),
	Vector3.new(58, 0, 58),
}) do
	local pole = makePart(map, "Plaza Street Lamp " .. i, Vector3.new(0.8, 13, 0.8),
		CFrame.new(spawnX + offset.X, 6.9, spawnZ + offset.Z),
		Enum.Material.Metal, Color3.fromRGB(45, 48, 52), true)
	local lamp = makePart(map, "Plaza Lamp Head " .. i, Vector3.new(3, 0.6, 1.4),
		CFrame.new(spawnX + offset.X, 13.5, spawnZ + offset.Z),
		Enum.Material.Metal, Color3.fromRGB(225, 205, 150), false)
	local light = Instance.new("PointLight")
	light.Brightness = 1.5
	light.Range = 22
	light.Color = Color3.fromRGB(255, 224, 170)
	light.Parent = lamp
end

local spawn = Instance.new("SpawnLocation")
spawn.Name = "Moscow Test Spawn"
spawn.Size = Vector3.new(12, 0.5, 12)
spawn.Position = Vector3.new(spawnX, 0.62, spawnZ) + MAP_OFFSET
spawn.Anchored = true
spawn.Neutral = true
spawn.AllowTeamChangeOnTouch = false
spawn.Material = Enum.Material.SmoothPlastic
spawn.Transparency = 1
spawn.CanCollide = false
spawn.Parent = map

local function bindPlayer(player)
	player.RespawnLocation = spawn

	player.CharacterAdded:Connect(function(character)
		local root = character:WaitForChild("HumanoidRootPart", 10)
		if root then
			task.wait(0.5)
			if character.Parent then
				character:PivotTo(CFrame.new(spawnX, 5, spawnZ) + MAP_OFFSET)
			end
		end
	end)

	if player.Character then
		task.spawn(function()
			local root = player.Character:WaitForChild("HumanoidRootPart", 10)
			if root and player.Character.Parent then
				task.wait(0.5)
				player.Character:PivotTo(CFrame.new(spawnX, 6, 0))
			end
		end)
	end
end

Players.PlayerAdded:Connect(bindPlayer)

for _, player in ipairs(Players:GetPlayers()) do
	bindPlayer(player)
end

print("========================================")
print("COBALT CITY RP — MOSCOW TEST MAP 0.5")
print("Road segments: " .. tostring(#(DATA.Roads or {})))
print("Buildings in source: " .. tostring(#(DATA.Buildings or {})))
print("Buildings skipped due to overlap: " .. tostring(skippedOverlapping))
print("Buildings created: " .. tostring(#acceptedFootprints))
print("Parks: " .. tostring(#(DATA.Parks or {})))
print("Water areas: " .. tostring(#(DATA.Water or {})))
print("Moscow map offset: " .. tostring(MAP_OFFSET))
print("Old CobaltCityMap was preserved and is spatially separated.")
print("========================================")
