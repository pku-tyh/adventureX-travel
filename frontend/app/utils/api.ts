// @/app/utils/api.ts

const API_BASE_URL = 'http://47.236.129.49:8011';

export async function getNewUserId(): Promise<number> {
  try {
    const response = await fetch(`${API_BASE_URL}/new_user`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data.new_id;
  } catch (error) {
    console.error('Error in getNewUserId:', error);
    throw error;
  }
}

export async function getPinInfo(userId: number, location: { lat: number; lng: number }) {
  try {
    const locationString = `${location.lng},${location.lat}`;
    const response = await fetch(`${API_BASE_URL}/pin_info_detailed?userid=${userId}&location=${locationString}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error in getPinInfo:', error);
    throw error;
  }
}

export async function getPinInfoBrief(userId: number, location: { lat: number; lng: number }) {
  try {
    const locationString = `${location.lng},${location.lat}`;
    const response = await fetch(`${API_BASE_URL}/pin_info_brief?userid=${userId}&location=${locationString}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error in getPinInfoBrief:', error);
    throw error;
  }
}
