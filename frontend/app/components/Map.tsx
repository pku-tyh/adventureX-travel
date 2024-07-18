// @/app/components/Map
'use client'

import { useEffect, useRef, useState } from 'react';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import { fromLonLat, toLonLat } from 'ol/proj';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import { Vector as VectorLayer } from 'ol/layer';
import { Vector as VectorSource } from 'ol/source';
import { Circle, Fill, Icon, Stroke, Style, Text } from 'ol/style';
import LineString from 'ol/geom/LineString';

const DISTANCE_MULTIPLIER = 10000 * 0.3;

export default function MapComponent({ userId, initialPosition, onPinInfoUpdate }) {
  const [map, setMap] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState(null);
  const [dragEnd, setDragEnd] = useState(null);
  const [showBubble, setShowBubble] = useState(true);
  const markerRef = useRef(null);
  const [roadData, setRoadData] = useState(null);
  const [mapPins, setMapPins] = useState([]);

  useEffect(() => {
    const newMap = new Map({
      target: 'map',
      layers: [
        new TileLayer({
          source: new OSM({
            attributions: [] // Remove OpenStreetMap contributors
          })
        })
      ],
      view: new View({
        center: fromLonLat(initialPosition),
        zoom: 12
      }),
      controls: [] // Remove all default controls including zoom
    });

    const marker = new Feature({
      geometry: new Point(fromLonLat(initialPosition))
    });

    marker.setStyle(new Style({
      image: new Icon({
        src: '/images/ai.jpg',
        scale: 0.3
      })
    }));

    markerRef.current = marker;

    const vectorSource = new VectorSource({
      features: [marker]
    });

    const vectorLayer = new VectorLayer({
      source: vectorSource
    });

    newMap.addLayer(vectorLayer);

    setMap(newMap);

    return () => {
      newMap.setTarget(undefined);
    };
  }, [initialPosition]);

  useEffect(() => {
    if (!map) return;

    const handlePointerDown = (e) => {
      const feature = map.forEachFeatureAtPixel(e.pixel, (feature) => feature);
      if (feature === markerRef.current) {
        setIsDragging(true);
        setShowBubble(false);
        setDragStart(e.coordinate);
        map.getTargetElement().style.cursor = 'grabbing';
        e.preventDefault();
      }
    };

    const handlePointerMove = (e) => {
      if (isDragging) {
        setDragEnd(e.coordinate);
      }
    };

    const handlePointerUp = () => {
      if (isDragging) {
        setIsDragging(false);
        map.getTargetElement().style.cursor = 'default';
        if (dragStart && dragEnd) {
          launchTarget();
        }
      }
    };

    map.on('pointerdown', handlePointerDown);
    map.on('pointermove', handlePointerMove);
    map.on('pointerup', handlePointerUp);

    return () => {
      map.un('pointerdown', handlePointerDown);
      map.un('pointermove', handlePointerMove);
      map.un('pointerup', handlePointerUp);
    };
  }, [map, isDragging, dragStart, dragEnd]);

  const launchTarget = async () => {
    if (!map || !dragStart || !dragEnd) return;

    const vectorSource = map.getLayers().getArray().find((layer) => layer instanceof VectorLayer)?.getSource();
    if (!vectorSource) return;

    const startPoint = markerRef.current.getGeometry().getCoordinates();
    const dragVector = [dragEnd[0] - dragStart[0], dragEnd[1] - dragStart[1]];

    const endPoint = [
      startPoint[0] - dragVector[0] * DISTANCE_MULTIPLIER,
      startPoint[1] - dragVector[1] * DISTANCE_MULTIPLIER
    ];

    vectorSource.clear();

    const targetMarker = new Feature({
      geometry: new Point(endPoint)
    });
    targetMarker.setStyle(new Style({
      image: new Icon({
        src: '/images/target.png',
        scale: 0.3
      })
    }));
    vectorSource.addFeature(targetMarker);

    const arrowLine = new Feature({
      geometry: new LineString(createParabolicCurve(startPoint, endPoint))
    });
    arrowLine.setStyle(new Style({
      stroke: new Stroke({
        color: '#0000FF',
        width: 2,
        lineDash: [5, 5]
      })
    }));
    vectorSource.addFeature(arrowLine);

    map.getView().fit(vectorSource.getExtent(), { padding: [50, 50, 50, 50] });

    const [lon, lat] = toLonLat(endPoint);
    const [fromLon, fromLat] = toLonLat(startPoint);

    try {
      const response = await fetch(`http://47.236.129.49:8011/build_road?userid=${userId}&from_location=${fromLon},${fromLat}&to_location=${lon},${lat}`);
      const data = await response.json();
      setRoadData(data.road);
      setMapPins(data.map_pins);
      drawRoadAndPins(data.road, data.map_pins, vectorSource);

      // 移除蓝色虚线抛物线
      vectorSource.removeFeature(arrowLine);
    } catch (error) {
      console.error('Error fetching road data:', error);
    }
  };

  const createParabolicCurve = (start, end) => {
    const numPoints = 100;
    const curve = [];
    const dx = end[0] - start[0];
    const dy = end[1] - start[1];
    const distance = Math.sqrt(dx * dx + dy * dy);

    const midX = (start[0] + end[0]) / 2;
    const midY = (start[1] + end[1]) / 2;
    const controlHeight = distance * 0.2;

    const perpX = -dy / distance;
    const perpY = dx / distance;

    const controlX = midX + perpX * controlHeight;
    const controlY = midY + perpY * controlHeight;

    for (let i = 0; i < numPoints; i++) {
      const t = i / (numPoints - 1);
      const x = Math.pow(1 - t, 2) * start[0] +
        2 * (1 - t) * t * controlX +
        Math.pow(t, 2) * end[0];
      const y = Math.pow(1 - t, 2) * start[1] +
        2 * (1 - t) * t * controlY +
        Math.pow(t, 2) * end[1];

      curve.push([x, y]);
    }
    return curve;
  };

  const drawRoadAndPins = async (road, pins, vectorSource) => {
    // 绘制路线（保持不变）
    const roadFeature = new Feature({
      geometry: new LineString(road.map(coord => fromLonLat(coord)))
    });
    roadFeature.setStyle(new Style({
      stroke: new Stroke({
        color: '#0000FF', // 蓝色
        width: 3
      })
    }));
    vectorSource.addFeature(roadFeature);
  
    // 创建一个带有白色边框和圆角的正方形图标
    const createCustomIcon = (src, size = 80) => {
      return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
  
        // 绘制白色背景和边框
        ctx.beginPath();
        ctx.roundRect(0, 0, size, size, 5); // 5px 圆角
        ctx.fillStyle = 'white';
        ctx.fill();
  
        // 创建稍小的矩形裁剪区域
        ctx.beginPath();
        ctx.roundRect(3, 3, size - 6, size - 6, 3);
        ctx.clip();
  
        // 加载并绘制图片
        const img = new Image();
        img.onload = () => {
          ctx.drawImage(img, 3, 3, size - 6, size - 6);
          resolve(canvas);
        };
        img.src = src;
      });
    };
  
    // 处理城市名称
    const processName = (name) => {
      const parts = name.split('-');
      return parts.length > 1 ? parts[parts.length - 1] : name;
    };
  
    // 去掉第一个和最后一个城市
    const middlePins = pins.slice(1, -1);
  
    // 添加城市标记
    for (const pin of middlePins) {
      let customIcon = await createCustomIcon('/images/city.png');
      let pinInfo = null;
  
      const pinFeature = new Feature({
        geometry: new Point(fromLonLat(pin.location))
      });
  
      const updateStyle = (icon, name) => {
        pinFeature.setStyle(new Style({
          image: new Icon({
            img: icon,
            imgSize: [80, 80],
            scale: 0.75,
            anchor: [0.5, 1],
            anchorXUnits: 'fraction',
            anchorYUnits: 'fraction',
          }),
          text: new Text({
            text: processName(name),
            font: 'bold 14px Arial',
            fill: new Fill({ color: '#FFFFFF' }),
            stroke: new Stroke({ color: '#000000', width: 3 }),
            offsetY: 20,
            textAlign: 'center',
            textBaseline: 'top',
            padding: [3, 3, 3, 3],
            backgroundFill: new Fill({ color: 'rgba(0, 0, 0, 0.7)' }),
            backgroundStroke: new Stroke({ color: '#000000', width: 1 })
          })
        }));
      };
  
      updateStyle(customIcon, pin.name);
      vectorSource.addFeature(pinFeature);
  
      // 添加白色圆点
      const dotFeature = new Feature({
        geometry: new Point(fromLonLat(pin.location))
      });
      dotFeature.setStyle(new Style({
        image: new Circle({
          radius: 4,
          fill: new Fill({ color: '#fff' }),
          stroke: new Stroke({ color: '#333', width: 1 })
        })
      }));
      vectorSource.addFeature(dotFeature);
  
      // 请求 pin 信息并更新图标
      pinInfo = await fetchPinInfo(pin.location);
      if (pinInfo) {
        customIcon = await createCustomIcon(pinInfo.image);
        updateStyle(customIcon, pinInfo.name);
        onPinInfoUpdate(pinInfo);
      }
    }
  
    // 调整视图以适应所有特征
    map.getView().fit(vectorSource.getExtent(), { padding: [50, 50, 50, 50] });
  };

  const getBubblePosition = () => {
    if (map && markerRef.current) {
      const coords = markerRef.current.getGeometry().getCoordinates();
      const pixel = map.getPixelFromCoordinate(coords);
      if (pixel) {
        return {
          top: `${pixel[1] + 30}px`,
          left: `${pixel[0] - 60}px`,
        };
      }
    }
    // 如果无法计算位置，返回默认位置（地图中心偏下）
    return {
      top: '60%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
    };
  };

  const fetchPinInfo = async (location, maxRetries = 50, retryDelay = 5000) => {
    let retries = 0;
    while (retries < maxRetries) {
      try {
        const response = await fetch(`http://47.236.129.49:8011/pin_info_brief?userid=${userId}&location=${location[0]},${location[1]}`);
        const data = await response.json();
        if (data !== null) {
          return data;
        }
        console.log(`Received null response, retrying... (Attempt ${retries + 1}/${maxRetries})`);
      } catch (error) {
        console.error('Error fetching pin info:', error);
      }
      retries++;
      if (retries < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
    console.error(`Failed to fetch pin info after ${maxRetries} attempts`);
    return null;
  };

  return (
    <div className='h-screen relative'>
      <div id="map" className="w-full h-full"></div>
      {isDragging && markerRef.current && map && (
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
          <div
            className="absolute w-48 h-48 rounded-full border-2 border-blue-500 opacity-50 bg-blue-200 bg-opacity-25"
            style={{
              top: `${map.getPixelFromCoordinate(markerRef.current.getGeometry().getCoordinates())[1] - 96}px`,
              left: `${map.getPixelFromCoordinate(markerRef.current.getGeometry().getCoordinates())[0] - 96}px`,
            }}
          ></div>
        </div>
      )}
      {showBubble && (
        <div
          className="absolute bg-white p-2 rounded shadow z-50"
          style={getBubblePosition()}
        >
          拖动我<br />选择想去的方向
        </div>
      )}
    </div>
  );
}
