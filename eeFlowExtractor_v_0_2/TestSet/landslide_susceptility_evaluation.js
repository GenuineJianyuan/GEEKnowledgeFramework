var LULC = ee.Image("users/region/XunwuCounty/Xunwu"),
    boundary = ee.FeatureCollection("users/region/XunwuCounty/XunwuBoundary");

// // 使用remap()方法将原始值替换为目标值
var remappedImage = LULC.remap([1, 2,3,6,8,9], [0.33,0.60,0.02,0,0.04,0.01], 0);

var landsat=ee.Image("users/region/XunwuCounty/Landsat_2018").clip(boundary)

// 计算NDVI
var ndvi = landsat.normalizedDifference(['B5', 'B4']);
// 添加 NDVI 到地图

// 加载SRTM Digital Elevation Model数据
var dem = ee.Image('USGS/SRTMGL1_003');
// 计算坡度
var slope = ee.Terrain.slope(dem);

// 创建一个条件图像
var slope_categories = slope.expression(
    "b('slope') < 20 ? 0.65 :" +
    "b('slope') < 30 ? 0.31 :" +
    "b('slope') < 40 ? 0.02 :" +
    "b('slope') < 50 ? 0.01 :" +
    "0"
).clip(boundary);

var result=ndvi.multiply(1.5).add(slope_categories.multiply(6.2)).add(remappedImage.multiply(2.3))

Map.addLayer(result, {min: 5.3, max: 7, palette: [  'green', 'lightgreen', 'yellow', 'red']})
