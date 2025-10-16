/**
 * Dynamic Filters Manager
 * Handles dynamic population of filter dropdowns and their interactions
 */

class DynamicFiltersManager {
    constructor() {
        this.filterData = {
            makes: [],
            models: [],
            cities: [],
            years: [],
            bodyTypes: [],
            priceRange: { min: 0, max: 200000 }
        };
        
        this.selectedFilters = {
            makes: [],
            models: [],
            cities: [],
            years: [],
            bodyTypes: [],
            priceMin: null,
            priceMax: null,
            yearMin: null,
            yearMax: null,
            mileageMax: null,
            fuelEconomyMin: null
        };
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadFilterData();
            this.populateFilters();
            this.setupEventListeners();
        } catch (error) {
            console.error('Failed to initialize dynamic filters:', error);
        }
    }
    
    async loadFilterData() {
        try {
            const response = await fetch('/api/listings/filter-data/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.filterData = {
                makes: data.makes || [],
                models: data.models || [],
                cities: data.cities || [],
                years: data.years || [],
                bodyTypes: data.body_types || [],
                priceRange: data.price_range || { min: 0, max: 200000 }
            };
            
            console.log('Filter data loaded:', this.filterData);
        } catch (error) {
            console.error('Error loading filter data:', error);
            // Use fallback data if API fails
            this.setFallbackData();
        }
    }
    
    setFallbackData() {
        this.filterData = {
            makes: [
                { name: 'Acura', count: 1 },
                { name: 'Audi', count: 58 },
                { name: 'BMW', count: 45 },
                { name: 'Mercedes-Benz', count: 32 },
                { name: 'Tesla', count: 28 },
                { name: 'Porsche', count: 15 },
                { name: 'Lexus', count: 22 },
                { name: 'Jaguar', count: 8 },
                { name: 'Range Rover', count: 6 },
                { name: 'Rolls Royce', count: 10 }
            ],
            models: [],
            cities: [
                { name: 'Los Angeles', count: 45 },
                { name: 'Beverly Hills', count: 32 },
                { name: 'Manhattan', count: 28 },
                { name: 'San Jose', count: 22 },
                { name: 'Miami Beach', count: 18 },
                { name: 'Houston', count: 15 },
                { name: 'Chicago', count: 12 },
                { name: 'Scottsdale', count: 10 }
            ],
            years: Array.from({ length: 25 }, (_, i) => ({ year: 2024 - i, count: Math.floor(Math.random() * 20) + 1 })),
            bodyTypes: [
                { name: 'SUV', count: 85 },
                { name: 'Sedan', count: 65 },
                { name: 'Coupe', count: 45 },
                { name: 'Convertible', count: 25 },
                { name: 'Hatchback', count: 15 },
                { name: 'Wagon', count: 8 }
            ],
            priceRange: { min: 0, max: 500000 }
        };
    }
    
    populateFilters() {
        this.populateMakeFilter();
        this.populateBodyTypeFilter();
        this.populateCityFilter();
        this.updatePriceRange();
        this.updateYearRange();
    }
    
    populateMakeFilter() {
        // Find make filter section by looking for summary containing "Make"
        const filterSections = document.querySelectorAll('.filter-section');
        let makeFilterContent = null;
        
        for (const section of filterSections) {
            const summary = section.querySelector('summary');
            if (summary && summary.textContent.includes('Make')) {
                makeFilterContent = section.querySelector('.filter-content');
                break;
            }
        }
        
        if (!makeFilterContent) return;
        
        makeFilterContent.innerHTML = '';
        
        this.filterData.makes.forEach(make => {
            const label = document.createElement('label');
            label.innerHTML = `
                <input type="checkbox" value="${make.name}" data-filter="make"> 
                ${make.name} ${make.count ? `(${make.count})` : ''}
            `;
            makeFilterContent.appendChild(label);
        });
    }
    
    populateBodyTypeFilter() {
        // Find body type filter section by looking for summary containing "Body Type"
        const filterSections = document.querySelectorAll('.filter-section');
        let bodyTypeFilterContent = null;
        
        for (const section of filterSections) {
            const summary = section.querySelector('summary');
            if (summary && summary.textContent.includes('Body Type')) {
                bodyTypeFilterContent = section.querySelector('.filter-content');
                break;
            }
        }
        
        if (!bodyTypeFilterContent) return;
        
        bodyTypeFilterContent.innerHTML = '';
        
        this.filterData.bodyTypes.forEach(bodyType => {
            const label = document.createElement('label');
            label.innerHTML = `
                <input type="checkbox" value="${bodyType.name}" data-filter="bodyType"> 
                ${bodyType.name} ${bodyType.count ? `(${bodyType.count})` : ''}
            `;
            bodyTypeFilterContent.appendChild(label);
        });
    }
    
    populateCityFilter() {
        // Find or create city filter section
        const filterSections = document.querySelectorAll('.filter-section');
        let cityFilterSection = null;
        
        for (const section of filterSections) {
            const summary = section.querySelector('summary');
            if (summary && summary.textContent.includes('City')) {
                cityFilterSection = section;
                break;
            }
        }
        
        if (!cityFilterSection) {
            // Create city filter section if it doesn't exist
            const filtersContainer = document.querySelector('.filters');
            if (filtersContainer) {
                cityFilterSection = document.createElement('details');
                cityFilterSection.className = 'filter-section';
                cityFilterSection.innerHTML = `
                    <summary>City <span class="arrow">▼</span></summary>
                    <div class="filter-content"></div>
                `;
                // Insert after Body Type filter
                const allFilterSections = document.querySelectorAll('.filter-section');
                let bodyTypeFilter = null;
                
                for (const section of allFilterSections) {
                    const summary = section.querySelector('summary');
                    if (summary && summary.textContent.includes('Body Type')) {
                        bodyTypeFilter = section;
                        break;
                    }
                }
                
                if (bodyTypeFilter) {
                    bodyTypeFilter.insertAdjacentElement('afterend', cityFilterSection);
                } else {
                    filtersContainer.appendChild(cityFilterSection);
                }
            }
        }
        
        const cityFilterContent = cityFilterSection?.querySelector('.filter-content');
        if (!cityFilterContent) return;
        
        cityFilterContent.innerHTML = '';
        
        this.filterData.cities.forEach(city => {
            const label = document.createElement('label');
            label.innerHTML = `
                <input type="checkbox" value="${city.name}" data-filter="city"> 
                ${city.name} ${city.count ? `(${city.count})` : ''}
            `;
            cityFilterContent.appendChild(label);
        });
    }
    
    updatePriceRange() {
        const priceSlider = document.getElementById('priceSlider');
        const priceValue = document.getElementById('priceValue');
        
        if (priceSlider && this.filterData.priceRange) {
            priceSlider.min = this.filterData.priceRange.min;
            priceSlider.max = this.filterData.priceRange.max;
            priceSlider.value = Math.floor(this.filterData.priceRange.max / 2);
            
            if (priceValue) {
                priceValue.textContent = this.formatPrice(priceSlider.value);
            }
        }
    }
    
    updateYearRange() {
        const yearSlider = document.getElementById('yearSlider');
        const yearValue = document.getElementById('yearValue');
        
        if (yearSlider && this.filterData.years.length > 0) {
            const minYear = Math.min(...this.filterData.years.map(y => y.year || y));
            const maxYear = Math.max(...this.filterData.years.map(y => y.year || y));
            
            yearSlider.min = minYear;
            yearSlider.max = maxYear;
            yearSlider.value = maxYear - 2; // Default to 2 years ago
            
            if (yearValue) {
                yearValue.textContent = yearSlider.value;
            }
        }
    }
    
    setupEventListeners() {
        // Checkbox filters
        document.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox' && e.target.dataset.filter) {
                this.handleCheckboxFilter(e.target);
            }
        });
        
        // Price slider
        const priceSlider = document.getElementById('priceSlider');
        if (priceSlider) {
            priceSlider.addEventListener('input', (e) => {
                const priceValue = document.getElementById('priceValue');
                if (priceValue) {
                    priceValue.textContent = this.formatPrice(e.target.value);
                }
                this.selectedFilters.priceMax = parseInt(e.target.value);
                this.debounceFilterUpdate();
            });
        }
        
        // Year slider
        const yearSlider = document.getElementById('yearSlider');
        if (yearSlider) {
            yearSlider.addEventListener('input', (e) => {
                const yearValue = document.getElementById('yearValue');
                if (yearValue) {
                    yearValue.textContent = e.target.value;
                }
                this.selectedFilters.yearMin = parseInt(e.target.value);
                this.debounceFilterUpdate();
            });
        }
        
        // Mileage slider
        const mileageSlider = document.getElementById('mileageSlider');
        if (mileageSlider) {
            mileageSlider.addEventListener('input', (e) => {
                const mileageValue = document.getElementById('mileageValue');
                if (mileageValue) {
                    mileageValue.textContent = this.formatMileage(e.target.value);
                }
                this.selectedFilters.mileageMax = parseInt(e.target.value);
                this.debounceFilterUpdate();
            });
        }
        
        // Fuel economy slider
        const fuelEconomySlider = document.getElementById('fuelEconomySlider');
        if (fuelEconomySlider) {
            fuelEconomySlider.addEventListener('input', (e) => {
                const fuelEconomyValue = document.getElementById('fuelEconomyValue');
                if (fuelEconomyValue) {
                    fuelEconomyValue.textContent = `${e.target.value} MPG`;
                }
                this.selectedFilters.fuelEconomyMin = parseInt(e.target.value);
                this.debounceFilterUpdate();
            });
        }
        
        // Price input fields
        const minPriceInput = document.getElementById('minPrice');
        const maxPriceInput = document.getElementById('maxPrice');
        
        if (minPriceInput) {
            minPriceInput.addEventListener('change', (e) => {
                this.selectedFilters.priceMin = this.parsePrice(e.target.value);
                this.debounceFilterUpdate();
            });
        }
        
        if (maxPriceInput) {
            maxPriceInput.addEventListener('change', (e) => {
                this.selectedFilters.priceMax = this.parsePrice(e.target.value);
                this.debounceFilterUpdate();
            });
        }
        
        // Make selection change - load models
        document.addEventListener('change', async (e) => {
            if (e.target.dataset.filter === 'make') {
                await this.loadModelsForSelectedMakes();
            }
        });
    }
    
    handleCheckboxFilter(checkbox) {
        const filterType = checkbox.dataset.filter;
        const value = checkbox.value;
        
        if (checkbox.checked) {
            if (!this.selectedFilters[filterType + 's']) {
                this.selectedFilters[filterType + 's'] = [];
            }
            this.selectedFilters[filterType + 's'].push(value);
        } else {
            if (this.selectedFilters[filterType + 's']) {
                this.selectedFilters[filterType + 's'] = this.selectedFilters[filterType + 's'].filter(v => v !== value);
            }
        }
        
        this.debounceFilterUpdate();
    }
    
    async loadModelsForSelectedMakes() {
        const selectedMakes = this.selectedFilters.makes;
        if (selectedMakes.length === 0) {
            this.populateModelFilter([]);
            return;
        }
        
        try {
            const makeParams = selectedMakes.map(make => `make=${encodeURIComponent(make)}`).join('&');
            const response = await fetch(`/api/listings/models-by-make/?${makeParams}`);
            
            if (response.ok) {
                const data = await response.json();
                this.populateModelFilter(data.models || []);
            }
        } catch (error) {
            console.error('Error loading models:', error);
        }
    }
    
    populateModelFilter(models) {
        // Find or create model filter section
        const filterSections = document.querySelectorAll('.filter-section');
        let modelFilterSection = null;
        
        for (const section of filterSections) {
            const summary = section.querySelector('summary');
            if (summary && summary.textContent.includes('Model')) {
                modelFilterSection = section;
                break;
            }
        }
        
        if (!modelFilterSection) {
            // Create model filter section if it doesn't exist
            const filtersContainer = document.querySelector('.filters');
            if (filtersContainer) {
                modelFilterSection = document.createElement('details');
                modelFilterSection.className = 'filter-section';
                modelFilterSection.innerHTML = `
                    <summary>Model <span class="arrow">▼</span></summary>
                    <div class="filter-content"></div>
                `;
                // Insert after Make filter
                const allFilterSections = document.querySelectorAll('.filter-section');
                let makeFilter = null;
                
                for (const section of allFilterSections) {
                    const summary = section.querySelector('summary');
                    if (summary && summary.textContent.includes('Make')) {
                        makeFilter = section;
                        break;
                    }
                }
                
                if (makeFilter) {
                    makeFilter.insertAdjacentElement('afterend', modelFilterSection);
                } else {
                    filtersContainer.appendChild(modelFilterSection);
                }
            }
        }
        
        const modelFilterContent = modelFilterSection?.querySelector('.filter-content');
        if (!modelFilterContent) return;
        
        modelFilterContent.innerHTML = '';
        
        if (models.length === 0) {
            modelFilterContent.innerHTML = '<p class="no-models">Select a make to see models</p>';
            return;
        }
        
        models.forEach(model => {
            const label = document.createElement('label');
            label.innerHTML = `
                <input type="checkbox" value="${model.name}" data-filter="model"> 
                ${model.name} ${model.count ? `(${model.count})` : ''}
            `;
            modelFilterContent.appendChild(label);
        });
    }
    
    debounceFilterUpdate() {
        clearTimeout(this.filterUpdateTimeout);
        this.filterUpdateTimeout = setTimeout(() => {
            this.notifyFilterChange();
        }, 300);
    }
    
    notifyFilterChange() {
        // Emit custom event for car grid to listen to
        const event = new CustomEvent('filtersChanged', {
            detail: { filters: this.getActiveFilters() }
        });
        document.dispatchEvent(event);
    }
    
    getActiveFilters() {
        const filters = {};
        
        // Add non-empty array filters
        Object.keys(this.selectedFilters).forEach(key => {
            const value = this.selectedFilters[key];
            if (Array.isArray(value) && value.length > 0) {
                filters[key] = value;
            } else if (value !== null && value !== undefined && !Array.isArray(value)) {
                filters[key] = value;
            }
        });
        
        return filters;
    }
    
    // Utility methods
    formatPrice(value) {
        const price = parseInt(value);
        if (price >= 1000000) {
            return `$${(price / 1000000).toFixed(1)}M`;
        } else if (price >= 1000) {
            return `$${(price / 1000).toFixed(0)}k`;
        } else {
            return `$${price}`;
        }
    }
    
    formatMileage(value) {
        const mileage = parseInt(value);
        if (mileage >= 1000) {
            return `${(mileage / 1000).toFixed(0)}k mi`;
        } else {
            return `${mileage} mi`;
        }
    }
    
    parsePrice(priceStr) {
        if (!priceStr) return null;
        
        // Remove currency symbols and commas
        const cleanStr = priceStr.replace(/[$,]/g, '');
        const price = parseFloat(cleanStr);
        
        return isNaN(price) ? null : price;
    }
    
    // Public methods for external use
    clearAllFilters() {
        // Reset all filters
        this.selectedFilters = {
            makes: [],
            models: [],
            cities: [],
            years: [],
            bodyTypes: [],
            priceMin: null,
            priceMax: null,
            yearMin: null,
            yearMax: null,
            mileageMax: null,
            fuelEconomyMin: null
        };
        
        // Clear all checkboxes
        document.querySelectorAll('input[type="checkbox"][data-filter]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Reset sliders to default values
        this.resetSliders();
        
        // Notify change
        this.notifyFilterChange();
    }
    
    resetSliders() {
        const priceSlider = document.getElementById('priceSlider');
        const yearSlider = document.getElementById('yearSlider');
        const mileageSlider = document.getElementById('mileageSlider');
        const fuelEconomySlider = document.getElementById('fuelEconomySlider');
        
        if (priceSlider) {
            priceSlider.value = Math.floor((parseInt(priceSlider.max) + parseInt(priceSlider.min)) / 2);
            const priceValue = document.getElementById('priceValue');
            if (priceValue) priceValue.textContent = this.formatPrice(priceSlider.value);
        }
        
        if (yearSlider) {
            yearSlider.value = parseInt(yearSlider.max) - 2;
            const yearValue = document.getElementById('yearValue');
            if (yearValue) yearValue.textContent = yearSlider.value;
        }
        
        if (mileageSlider) {
            mileageSlider.value = Math.floor((parseInt(mileageSlider.max) + parseInt(mileageSlider.min)) / 2);
            const mileageValue = document.getElementById('mileageValue');
            if (mileageValue) mileageValue.textContent = this.formatMileage(mileageSlider.value);
        }
        
        if (fuelEconomySlider) {
            fuelEconomySlider.value = Math.floor((parseInt(fuelEconomySlider.max) + parseInt(fuelEconomySlider.min)) / 2);
            const fuelEconomyValue = document.getElementById('fuelEconomyValue');
            if (fuelEconomyValue) fuelEconomyValue.textContent = `${fuelEconomySlider.value} MPG`;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dynamicFiltersManager = new DynamicFiltersManager();
});
