// Location Management Service

const COUNTRY_LIST = [
  { code: 'AF', name: 'Afghanistan' },
  { code: 'AX', name: 'Aland Islands' },
  { code: 'AL', name: 'Albania' },
  { code: 'DZ', name: 'Algeria' },
  { code: 'AS', name: 'American Samoa' },
  { code: 'AD', name: 'Andorra' },
  { code: 'AO', name: 'Angola' },
  { code: 'AI', name: 'Anguilla' },
  { code: 'AQ', name: 'Antarctica' },
  { code: 'AG', name: 'Antigua and Barbuda' },
  { code: 'AR', name: 'Argentina' },
  { code: 'AM', name: 'Armenia' },
  { code: 'AW', name: 'Aruba' },
  { code: 'AU', name: 'Australia' },
  { code: 'AT', name: 'Austria' },
  { code: 'AZ', name: 'Azerbaijan' },
  { code: 'BS', name: 'Bahamas' },
  { code: 'BH', name: 'Bahrain' },
  { code: 'BD', name: 'Bangladesh' },
  { code: 'BB', name: 'Barbados' },
  { code: 'BY', name: 'Belarus' },
  { code: 'BE', name: 'Belgium' },
  { code: 'BZ', name: 'Belize' },
  { code: 'BJ', name: 'Benin' },
  { code: 'BM', name: 'Bermuda' },
  { code: 'BT', name: 'Bhutan' },
  { code: 'BO', name: 'Bolivia' },
  { code: 'BQ', name: 'Bonaire, Sint Eustatius and Saba' },
  { code: 'BA', name: 'Bosnia and Herzegovina' },
  { code: 'BW', name: 'Botswana' },
  { code: 'BV', name: 'Bouvet Island' },
  { code: 'BR', name: 'Brazil' },
  { code: 'IO', name: 'British Indian Ocean Territory' },
  { code: 'BN', name: 'Brunei' },
  { code: 'BG', name: 'Bulgaria' },
  { code: 'BF', name: 'Burkina Faso' },
  { code: 'BI', name: 'Burundi' },
  { code: 'CV', name: 'Cabo Verde' },
  { code: 'KH', name: 'Cambodia' },
  { code: 'CM', name: 'Cameroon' },
  { code: 'CA', name: 'Canada' },
  { code: 'KY', name: 'Cayman Islands' },
  { code: 'CF', name: 'Central African Republic' },
  { code: 'TD', name: 'Chad' },
  { code: 'CL', name: 'Chile' },
  { code: 'CN', name: 'China' },
  { code: 'CX', name: 'Christmas Island' },
  { code: 'CC', name: 'Cocos (Keeling) Islands' },
  { code: 'CO', name: 'Colombia' },
  { code: 'KM', name: 'Comoros' },
  { code: 'CG', name: 'Congo' },
  { code: 'CD', name: 'Congo (Democratic Republic of the)' },
  { code: 'CK', name: 'Cook Islands' },
  { code: 'CR', name: 'Costa Rica' },
  { code: 'CI', name: "Cote d'Ivoire" },
  { code: 'HR', name: 'Croatia' },
  { code: 'CU', name: 'Cuba' },
  { code: 'CW', name: 'Curacao' },
  { code: 'CY', name: 'Cyprus' },
  { code: 'CZ', name: 'Czechia' },
  { code: 'DK', name: 'Denmark' },
  { code: 'DJ', name: 'Djibouti' },
  { code: 'DM', name: 'Dominica' },
  { code: 'DO', name: 'Dominican Republic' },
  { code: 'EC', name: 'Ecuador' },
  { code: 'EG', name: 'Egypt' },
  { code: 'SV', name: 'El Salvador' },
  { code: 'GQ', name: 'Equatorial Guinea' },
  { code: 'ER', name: 'Eritrea' },
  { code: 'EE', name: 'Estonia' },
  { code: 'SZ', name: 'Eswatini' },
  { code: 'ET', name: 'Ethiopia' },
  { code: 'FK', name: 'Falkland Islands' },
  { code: 'FO', name: 'Faroe Islands' },
  { code: 'FJ', name: 'Fiji' },
  { code: 'FI', name: 'Finland' },
  { code: 'FR', name: 'France' },
  { code: 'GF', name: 'French Guiana' },
  { code: 'PF', name: 'French Polynesia' },
  { code: 'TF', name: 'French Southern Territories' },
  { code: 'GA', name: 'Gabon' },
  { code: 'GM', name: 'Gambia' },
  { code: 'GE', name: 'Georgia' },
  { code: 'DE', name: 'Germany' },
  { code: 'GH', name: 'Ghana' },
  { code: 'GI', name: 'Gibraltar' },
  { code: 'GR', name: 'Greece' },
  { code: 'GL', name: 'Greenland' },
  { code: 'GD', name: 'Grenada' },
  { code: 'GP', name: 'Guadeloupe' },
  { code: 'GU', name: 'Guam' },
  { code: 'GT', name: 'Guatemala' },
  { code: 'GG', name: 'Guernsey' },
  { code: 'GN', name: 'Guinea' },
  { code: 'GW', name: 'Guinea-Bissau' },
  { code: 'GY', name: 'Guyana' },
  { code: 'HT', name: 'Haiti' },
  { code: 'HM', name: 'Heard Island and McDonald Islands' },
  { code: 'VA', name: 'Vatican City' },
  { code: 'HN', name: 'Honduras' },
  { code: 'HK', name: 'Hong Kong' },
  { code: 'HU', name: 'Hungary' },
  { code: 'IS', name: 'Iceland' },
  { code: 'IN', name: 'India' },
  { code: 'ID', name: 'Indonesia' },
  { code: 'IR', name: 'Iran' },
  { code: 'IQ', name: 'Iraq' },
  { code: 'IE', name: 'Ireland' },
  { code: 'IM', name: 'Isle of Man' },
  { code: 'IL', name: 'Israel' },
  { code: 'IT', name: 'Italy' },
  { code: 'JM', name: 'Jamaica' },
  { code: 'JP', name: 'Japan' },
  { code: 'JE', name: 'Jersey' },
  { code: 'JO', name: 'Jordan' },
  { code: 'KZ', name: 'Kazakhstan' },
  { code: 'KE', name: 'Kenya' },
  { code: 'KI', name: 'Kiribati' },
  { code: 'KP', name: 'Korea (North)' },
  { code: 'KR', name: 'Korea (South)' },
  { code: 'KW', name: 'Kuwait' },
  { code: 'KG', name: 'Kyrgyzstan' },
  { code: 'LA', name: 'Laos' },
  { code: 'LV', name: 'Latvia' },
  { code: 'LB', name: 'Lebanon' },
  { code: 'LS', name: 'Lesotho' },
  { code: 'LR', name: 'Liberia' },
  { code: 'LY', name: 'Libya' },
  { code: 'LI', name: 'Liechtenstein' },
  { code: 'LT', name: 'Lithuania' },
  { code: 'LU', name: 'Luxembourg' },
  { code: 'MO', name: 'Macao' },
  { code: 'MK', name: 'North Macedonia' },
  { code: 'MG', name: 'Madagascar' },
  { code: 'MW', name: 'Malawi' },
  { code: 'MY', name: 'Malaysia' },
  { code: 'MV', name: 'Maldives' },
  { code: 'ML', name: 'Mali' },
  { code: 'MT', name: 'Malta' },
  { code: 'MH', name: 'Marshall Islands' },
  { code: 'MQ', name: 'Martinique' },
  { code: 'MR', name: 'Mauritania' },
  { code: 'MU', name: 'Mauritius' },
  { code: 'YT', name: 'Mayotte' },
  { code: 'MX', name: 'Mexico' },
  { code: 'FM', name: 'Micronesia' },
  { code: 'MD', name: 'Moldova' },
  { code: 'MC', name: 'Monaco' },
  { code: 'MN', name: 'Mongolia' },
  { code: 'ME', name: 'Montenegro' },
  { code: 'MS', name: 'Montserrat' },
  { code: 'MA', name: 'Morocco' },
  { code: 'MZ', name: 'Mozambique' },
  { code: 'MM', name: 'Myanmar' },
  { code: 'NA', name: 'Namibia' },
  { code: 'NR', name: 'Nauru' },
  { code: 'NP', name: 'Nepal' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'NC', name: 'New Caledonia' },
  { code: 'NZ', name: 'New Zealand' },
  { code: 'NI', name: 'Nicaragua' },
  { code: 'NE', name: 'Niger' },
  { code: 'NG', name: 'Nigeria' },
  { code: 'NU', name: 'Niue' },
  { code: 'NF', name: 'Norfolk Island' },
  { code: 'MP', name: 'Northern Mariana Islands' },
  { code: 'NO', name: 'Norway' },
  { code: 'OM', name: 'Oman' },
  { code: 'PK', name: 'Pakistan' },
  { code: 'PW', name: 'Palau' },
  { code: 'PS', name: 'Palestine' },
  { code: 'PA', name: 'Panama' },
  { code: 'PG', name: 'Papua New Guinea' },
  { code: 'PY', name: 'Paraguay' },
  { code: 'PE', name: 'Peru' },
  { code: 'PH', name: 'Philippines' },
  { code: 'PN', name: 'Pitcairn' },
  { code: 'PL', name: 'Poland' },
  { code: 'PT', name: 'Portugal' },
  { code: 'PR', name: 'Puerto Rico' },
  { code: 'QA', name: 'Qatar' },
  { code: 'RE', name: 'Reunion' },
  { code: 'RO', name: 'Romania' },
  { code: 'RU', name: 'Russia' },
  { code: 'RW', name: 'Rwanda' },
  { code: 'BL', name: 'Saint Barthelemy' },
  { code: 'SH', name: 'Saint Helena, Ascension and Tristan da Cunha' },
  { code: 'KN', name: 'Saint Kitts and Nevis' },
  { code: 'LC', name: 'Saint Lucia' },
  { code: 'MF', name: 'Saint Martin (French part)' },
  { code: 'PM', name: 'Saint Pierre and Miquelon' },
  { code: 'VC', name: 'Saint Vincent and the Grenadines' },
  { code: 'WS', name: 'Samoa' },
  { code: 'SM', name: 'San Marino' },
  { code: 'ST', name: 'Sao Tome and Principe' },
  { code: 'SA', name: 'Saudi Arabia' },
  { code: 'SN', name: 'Senegal' },
  { code: 'RS', name: 'Serbia' },
  { code: 'SC', name: 'Seychelles' },
  { code: 'SL', name: 'Sierra Leone' },
  { code: 'SG', name: 'Singapore' },
  { code: 'SX', name: 'Sint Maarten (Dutch part)' },
  { code: 'SK', name: 'Slovakia' },
  { code: 'SI', name: 'Slovenia' },
  { code: 'SB', name: 'Solomon Islands' },
  { code: 'SO', name: 'Somalia' },
  { code: 'ZA', name: 'South Africa' },
  { code: 'GS', name: 'South Georgia and the South Sandwich Islands' },
  { code: 'SS', name: 'South Sudan' },
  { code: 'ES', name: 'Spain' },
  { code: 'LK', name: 'Sri Lanka' },
  { code: 'SD', name: 'Sudan' },
  { code: 'SR', name: 'Suriname' },
  { code: 'SJ', name: 'Svalbard and Jan Mayen' },
  { code: 'SE', name: 'Sweden' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'SY', name: 'Syria' },
  { code: 'TW', name: 'Taiwan' },
  { code: 'TJ', name: 'Tajikistan' },
  { code: 'TZ', name: 'Tanzania' },
  { code: 'TH', name: 'Thailand' },
  { code: 'TL', name: 'Timor-Leste' },
  { code: 'TG', name: 'Togo' },
  { code: 'TK', name: 'Tokelau' },
  { code: 'TO', name: 'Tonga' },
  { code: 'TT', name: 'Trinidad and Tobago' },
  { code: 'TN', name: 'Tunisia' },
  { code: 'TR', name: 'Turkey' },
  { code: 'TM', name: 'Turkmenistan' },
  { code: 'TC', name: 'Turks and Caicos Islands' },
  { code: 'TV', name: 'Tuvalu' },
  { code: 'UG', name: 'Uganda' },
  { code: 'UA', name: 'Ukraine' },
  { code: 'AE', name: 'United Arab Emirates' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'US', name: 'United States' },
  { code: 'UM', name: 'United States Minor Outlying Islands' },
  { code: 'UY', name: 'Uruguay' },
  { code: 'UZ', name: 'Uzbekistan' },
  { code: 'VU', name: 'Vanuatu' },
  { code: 'VE', name: 'Venezuela' },
  { code: 'VN', name: 'Vietnam' },
  { code: 'VG', name: 'British Virgin Islands' },
  { code: 'VI', name: 'US Virgin Islands' },
  { code: 'WF', name: 'Wallis and Futuna' },
  { code: 'EH', name: 'Western Sahara' },
  { code: 'YE', name: 'Yemen' },
  { code: 'ZM', name: 'Zambia' },
  { code: 'ZW', name: 'Zimbabwe' }
];

const COUNTRY_NAME_MAP = COUNTRY_LIST.reduce((acc, country) => {
  acc[country.code] = country.name;
  return acc;
}, {});

const DEFAULT_UNITS = { weight: 'kg', volume: 'ml', currency: 'USD' };

const UNIT_STANDARDS = {
  'US': { weight: 'lbs', volume: 'fl oz', currency: 'USD' },
  'GB': { weight: 'lbs', volume: 'fl oz', currency: 'GBP' },
  'CA': { weight: 'kg', volume: 'ml', currency: 'CAD' },
  'AU': { weight: 'kg', volume: 'ml', currency: 'AUD' },
  'IN': { weight: 'kg', volume: 'ml', currency: 'INR' },
  'DE': { weight: 'kg', volume: 'ml', currency: 'EUR' },
  'FR': { weight: 'kg', volume: 'ml', currency: 'EUR' },
  'JP': { weight: 'kg', volume: 'ml', currency: 'JPY' },
  'CN': { weight: 'kg', volume: 'ml', currency: 'CNY' },
  'MX': { weight: 'kg', volume: 'ml', currency: 'MXN' },
  'BR': { weight: 'kg', volume: 'ml', currency: 'BRL' }
};

function getUnitsForCountry(countryCode) {
  return UNIT_STANDARDS[countryCode] || DEFAULT_UNITS;
}

class LocationService {
  constructor() {
    this.location = null;
    this.country = null;
    this.units = null;
    this.loadFromStorage();
  }

  // Load location from localStorage
  loadFromStorage() {
    try {
      const stored = localStorage.getItem('userLocation');
      if (stored) {
        const data = JSON.parse(stored);
        this.location = data.location;
        this.country = data.country;
        this.units = data.units;
        console.log('✅ Loaded from storage:', { country: this.country, units: this.units });
        return data;
      }
    } catch (error) {
      console.error('Error loading location from storage:', error);
    }
    return null;
  }

  // Save location to localStorage
  saveToStorage() {
    try {
      const dataToSave = {
        location: this.location,
        country: this.country,
        units: this.units,
        timestamp: new Date().getTime()
      };
      console.log('💾 Saving to storage:', dataToSave);
      localStorage.setItem('userLocation', JSON.stringify(dataToSave));
      console.log('✅ Successfully saved to localStorage');
    } catch (error) {
      console.error('Error saving location to storage:', error);
    }
  }

  // Get user's current location
  getCurrentLocation() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          this.location = { latitude, longitude };
          resolve({ latitude, longitude });
        },
        (error) => {
          console.error('Geolocation error:', error);
          reject(error);
        }
      );
    });
  }

  // Get country from coordinates
  async getCountryFromCoordinates(latitude, longitude) {
    try {
      // Check if user is logged in to use backend API
      const response = await fetch('/api/location/country', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ latitude, longitude })
      });

      if (response.status === 401) {
        // Not logged in, detect locally
        return this.detectCountryLocally(latitude, longitude);
      }

      const data = await response.json();
      if (data.success) {
        this.country = data.country;
        this.units = data.units;
        this.saveToStorage();
        return data;
      }
      throw new Error(data.error);
    } catch (error) {
      console.error('Error getting country:', error);
      // Fall back to local detection
      return this.detectCountryLocally(latitude, longitude);
    }
  }

  // Local country detection based on coordinates
  detectCountryLocally(latitude, longitude) {
    const countryMap = {
      'IN': { lat: [6, 37], lon: [68, 98] },      // India - check first for priority
      'US': { lat: [24, 50], lon: [-125, -66] },  // USA (continental)
      'GB': { lat: [50, 59], lon: [-8, 2] },      // UK
      'CA': { lat: [41, 84], lon: [-141, -52] },  // Canada
      'AU': { lat: [-44, -10], lon: [113, 154] }, // Australia
      'DE': { lat: [47, 55], lon: [5, 15] },      // Germany
      'FR': { lat: [41, 51], lon: [-5, 10] },     // France
      'JP': { lat: [24, 46], lon: [122, 146] },   // Japan
      'CN': { lat: [18, 54], lon: [73, 135] },    // China
      'MX': { lat: [14, 33], lon: [-118, -86] },  // Mexico
      'BR': { lat: [-34, 6], lon: [-74, -34] }    // Brazil
    };

    let detectedCountry = 'US'; // Default
    
    // Check each country
    for (const [country, bounds] of Object.entries(countryMap)) {
      const [latMin, latMax] = bounds.lat;
      const [lonMin, lonMax] = bounds.lon;
      
      // Check if coordinates fall within bounds
      if (latitude >= latMin && latitude <= latMax && 
          longitude >= lonMin && longitude <= lonMax) {
        detectedCountry = country;
        console.log(`Location detected: ${country} (Lat: ${latitude}, Lon: ${longitude})`);
        break;
      }
    }

    this.country = detectedCountry;
    this.units = getUnitsForCountry(detectedCountry);
    this.location = { latitude, longitude, country: detectedCountry };
    this.saveToStorage();

    console.log(`Final detection: Country=${detectedCountry}, Units=`, this.units);

    return {
      success: true,
      country: detectedCountry,
      units: this.units,
      location: this.location
    };
  }

  // Get user's location settings
  async getUserLocation() {
    try {
      const response = await fetch('/api/user/location');
      const data = await response.json();
      if (data.success) {
        this.location = data.location;
        this.units = data.units;
        this.saveToStorage();
        return data;
      }
      throw new Error(data.error);
    } catch (error) {
      console.error('Error getting user location:', error);
      return this.loadFromStorage();
    }
  }

  // Request location permission and detect country
  async requestLocation() {
    try {
      const position = await this.getCurrentLocation();
      const locationData = await this.getCountryFromCoordinates(
        position.latitude,
        position.longitude
      );
      return locationData;
    } catch (error) {
      console.error('Location request failed:', error);
      // Use default if location fails
      this.country = 'US';
      this.units = { weight: 'lbs', volume: 'fl oz', currency: 'USD' };
      this.location = { country: 'US' };
      this.saveToStorage();
      return {
        success: true,
        country: 'US',
        units: this.units,
        location: this.location,
        default: true
      };
    }
  }

  // Convert units
  async convertUnits(value, fromUnit, toUnit) {
    try {
      const response = await fetch('/api/convert-units', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          value,
          from_unit: fromUnit,
          to_unit: toUnit
        })
      });

      const data = await response.json();
      if (data.success) {
        return data.converted_value;
      }
      throw new Error(data.error);
    } catch (error) {
      console.error('Error converting units:', error);
      throw error;
    }
  }

  // Get unit symbol for display
  getUnitSymbol(unit) {
    const symbols = {
      'kg': 'kg',
      'lbs': 'lbs',
      'ml': 'ml',
      'fl oz': 'fl oz',
      'USD': '$',
      'GBP': '£',
      'EUR': '€',
      'INR': '₹',
      'JPY': '¥',
      'CAD': '$',
      'AUD': '$',
      'MXN': '$',
      'BRL': 'R$',
      'CNY': '¥'
    };
    return symbols[unit] || unit;
  }

  // Format location display
  getLocationDisplay() {
    if (!this.location) return 'Location not set';
    const country = this.location.country || 'Unknown';
    const city = this.location.city || '';
    return `${city ? city + ', ' : ''}${country}`;
  }

  // Get currency symbol
  getCurrencySymbol() {
    if (!this.units || !this.units.currency) return '$';
    return this.getUnitSymbol(this.units.currency);
  }

  // Get weight unit
  getWeightUnit() {
    return this.units?.weight || 'kg';
  }

  // Get volume unit
  getVolumeUnit() {
    return this.units?.volume || 'ml';
  }
}

// Create global instance
const locationService = new LocationService();

function populateCountryOptions(selectElement, countries, selectedCode) {
  selectElement.innerHTML = '<option value="">-- Select Country --</option>';
  if (!countries.length) {
    const emptyOption = document.createElement('option');
    emptyOption.disabled = true;
    emptyOption.textContent = 'No matches';
    selectElement.appendChild(emptyOption);
    return;
  }

  countries.forEach((country) => {
    const option = document.createElement('option');
    option.value = country.code;
    option.textContent = country.name;
    selectElement.appendChild(option);
  });

  if (selectedCode) {
    selectElement.value = selectedCode;
  }
}

function initCountrySearch() {
  const searchInput = document.getElementById('countrySearch');
  const countrySelect = document.getElementById('countrySelect');
  if (!countrySelect) return;

  populateCountryOptions(countrySelect, COUNTRY_LIST);

  if (!searchInput) return;
  searchInput.addEventListener('input', () => {
    const query = searchInput.value.trim().toLowerCase();
    const filtered = COUNTRY_LIST.filter((country) =>
      country.name.toLowerCase().includes(query)
    );
    populateCountryOptions(countrySelect, filtered);
  });
}

// Show location permission modal on landing page
function showLocationModal() {
  // Clear existing location data to force re-detection
  localStorage.removeItem('userLocation');
  
  // Remove any existing modal
  const existingModal = document.getElementById('locationModal');
  if (existingModal) {
    existingModal.remove();
  }
  
  const modal = document.createElement('div');
  modal.className = 'location-modal-overlay';
  modal.id = 'locationModal';
  modal.innerHTML = `
    <div class="location-modal">
      <div class="location-modal-header">
        <i class="fas fa-map-marker-alt"></i>
        <h2>Select Your Location</h2>
      </div>
      <div class="location-modal-body">
        <p>Choose your country to get location-specific units and currency.</p>
        
        <div class="form-group" style="margin: 1.5rem 0;">
          <label for="countrySelect" style="display: block; margin-bottom: 0.5rem; font-weight: 600; color: #2b3a67;">
            <i class="fas fa-globe"></i> Select Your Country
          </label>
          <input
            type="text"
            id="countrySearch"
            class="country-search"
            placeholder="Search countries..."
            autocomplete="off"
          />
          <select id="countrySelect" class="country-select" size="10">
            <option value="">-- Select Country --</option>
          </select>
        </div>
        
        <div style="text-align: center; margin: 1rem 0;">
          <span style="color: #999;">OR</span>
        </div>
        
        <div class="location-benefits">
          <div class="benefit">
            <i class="fas fa-check-circle"></i>
            <span>Auto-detect from browser location</span>
          </div>
        </div>
      </div>
      <div class="location-modal-actions">
        <button class="btn btn-secondary" id="autoDetectBtn">
          <i class="fas fa-location-arrow"></i> Auto-Detect
        </button>
        <button class="btn btn-primary" id="saveLocationBtn">
          <i class="fas fa-check"></i> Save Selection
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  initCountrySearch();

  // Auto-detect button
  document.getElementById('autoDetectBtn').addEventListener('click', async () => {
    const btn = document.getElementById('autoDetectBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
    btn.disabled = true;
    
    try {
      const result = await locationService.requestLocation();
      console.log('Auto-detected location:', result);
      modal.remove();
      showLocationSuccess(result.location);
      // Trigger page update
      if (typeof updateLocationDisplay === 'function') {
        updateLocationDisplay();
      }
      // Update navigation links with location
      if (typeof updateNavigationLinks === 'function') {
        updateNavigationLinks();
      }
      // NO location.reload() - just close the modal and let user continue
    } catch (error) {
      console.error('Location request failed:', error);
      btn.innerHTML = originalText;
      btn.disabled = false;
      alert('Unable to detect location automatically. Please select your country manually from the dropdown.');
    }
  });

  function applyManualSelection(selectedCountry) {
    if (!selectedCountry) {
      alert('Please select a country from the dropdown.');
      return;
    }

    locationService.country = selectedCountry;
    locationService.units = getUnitsForCountry(selectedCountry);
    locationService.location = { country: selectedCountry };
    locationService.saveToStorage();

    console.log('✅ Manually selected country:', selectedCountry);
    console.log('✅ Units set to:', locationService.units);

    modal.remove();
    showLocationSuccess({ country: selectedCountry });

    // Trigger page update
    if (typeof updateLocationDisplay === 'function') {
      updateLocationDisplay();
    }
    
    // Update navigation links with location
    if (typeof updateNavigationLinks === 'function') {
      updateNavigationLinks();
    }
    
    // NO location.reload() - just close the modal and let user continue
  }

  // Save manual selection button
  document.getElementById('saveLocationBtn').addEventListener('click', () => {
    const selectedCountry = document.getElementById('countrySelect').value;
    applyManualSelection(selectedCountry);
  });

  const countrySelect = document.getElementById('countrySelect');
  countrySelect.addEventListener('dblclick', (event) => {
    if (event.target && event.target.tagName === 'OPTION') {
      applyManualSelection(countrySelect.value);
    }
  });
}

// Show location success message
function showLocationSuccess(location) {
  const countryName = COUNTRY_NAME_MAP[location?.country] || location?.country || 'Unknown';
  
  const toast = document.createElement('div');
  toast.className = 'location-toast success';
  toast.innerHTML = `
    <i class="fas fa-check-circle"></i>
    <span>Location set to: ${countryName}</span>
  `;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hide');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Initialize location on page load
document.addEventListener('DOMContentLoaded', () => {
  const isAuthPage = document.body.classList.contains('auth-page');
  const isLandingPage = document.body.classList.contains('landing-page');
  
  if (isLandingPage) {
    // Check if location was already set
    const storedLocation = locationService.loadFromStorage();
    if (!storedLocation || !storedLocation.location || !storedLocation.location.country) {
      // Show location modal on landing page
      setTimeout(() => {
        showLocationModal();
      }, 800);
    }
  } else if (!isAuthPage) {
    // On dashboard/other pages, load saved location
    locationService.getUserLocation().catch(err => {
      console.log('Using stored or default units');
    });
  }
});

// Add hidden input fields for location to login/signup forms
function attachLocationToForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return;

  const latitudeInput = document.createElement('input');
  latitudeInput.type = 'hidden';
  latitudeInput.name = 'latitude';
  latitudeInput.id = 'latitude';

  const longitudeInput = document.createElement('input');
  longitudeInput.type = 'hidden';
  longitudeInput.name = 'longitude';
  longitudeInput.id = 'longitude';

  const countryInput = document.createElement('input');
  countryInput.type = 'hidden';
  countryInput.name = 'country';
  countryInput.id = 'country';

  const cityInput = document.createElement('input');
  cityInput.type = 'hidden';
  cityInput.name = 'city';
  cityInput.id = 'city';

  form.appendChild(latitudeInput);
  form.appendChild(longitudeInput);
  form.appendChild(countryInput);
  form.appendChild(cityInput);

  form.addEventListener('submit', async (e) => {
    // Use stored location if available
    const storedLocation = locationService.loadFromStorage();
    if (storedLocation) {
      console.log('📍 Using stored location:', storedLocation);
      
      // Set coordinates if available
      if (storedLocation.location) {
        document.getElementById('latitude').value = storedLocation.location.latitude || '';
        document.getElementById('longitude').value = storedLocation.location.longitude || '';
        
        // Set city if available
        if (storedLocation.location.city) {
          document.getElementById('city').value = storedLocation.location.city;
        }
      }
      
      // Set country code (most important for units)
      if (storedLocation.country) {
        document.getElementById('country').value = storedLocation.country;
        console.log('✅ Country set to:', storedLocation.country);
      }
      
      return; // Form will submit normally
    }

    // Otherwise try to get location
    let userWantsLocation = false;
    try {
      userWantsLocation = localStorage.getItem('locationRequested') !== 'true';
    } catch (error) {
      // If storage is blocked (Simple Browser), skip location and submit normally.
      userWantsLocation = false;
    }

    if (userWantsLocation && navigator.geolocation) {
      e.preventDefault();
      
      try {
        const position = await locationService.getCurrentLocation();
        document.getElementById('latitude').value = position.latitude;
        document.getElementById('longitude').value = position.longitude;
        try {
          localStorage.setItem('locationRequested', 'true');
        } catch (error) {
          // Ignore storage failures and proceed with submit.
        }
        form.submit();
      } catch (error) {
        // Continue without location
        try {
          localStorage.setItem('locationRequested', 'true');
        } catch (error) {
          // Ignore storage failures and proceed with submit.
        }
        form.submit();
      }
    }
  });
}

// Export for use in other scripts
window.LocationService = LocationService;
window.locationService = locationService;
window.showLocationModal = showLocationModal;
window.attachLocationToForm = attachLocationToForm;
