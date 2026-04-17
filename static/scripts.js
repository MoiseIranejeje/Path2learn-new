const searchButton = document.getElementById('search-btn');
const recommendButton = document.getElementById('recommend-btn');
const searchQueryInput = document.getElementById('search-query');

if (searchButton) {
    searchButton.addEventListener('click', performSearch);
}

if (recommendButton) {
    recommendButton.addEventListener('click', performRecommendation);
}

if (searchQueryInput) {
    searchQueryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// Helper function for search
function performSearch() {
    const queryInput = document.getElementById('search-query');
    const educationProgramInput = document.getElementById('recommend-education');
    const provinceInput = document.getElementById('recommend-province');
    const resultsContainer = document.getElementById('search-results');
    const searchSection = document.getElementById('search');

    if (!queryInput || !educationProgramInput || !provinceInput || !resultsContainer || !searchSection) {
        return;
    }

    const query = queryInput.value;
    const educationProgram = educationProgramInput.value;
    const province = provinceInput.value;
    let url = `/search?query=${encodeURIComponent(query)}`;
    
    if (educationProgram) url += `&education_program=${encodeURIComponent(educationProgram)}`;
    if (province) url += `&province=${encodeURIComponent(province)}`;
    
    // Show loading state
    resultsContainer.innerHTML = `
        <div class="col-12 text-center py-10">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-gray-600">Searching for schools...</p>
        </div>
    `;
    
    // Scroll to results
    searchSection.scrollIntoView({ behavior: 'smooth' });
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            resultsContainer.innerHTML = '';
            if (data.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="col-12 text-center py-10">
                        <i class="fas fa-school text-gray-400 text-5xl mb-4"></i>
                        <h3 class="text-xl font-bold text-gray-700">No schools found</h3>
                        <p class="text-gray-500 mt-2">Try adjusting your search criteria</p>
                    </div>
                `;
            } else {
                data.forEach((school, index) => {
                    // Add animation delay for staggered effect
                    const delay = index * 100;
                    resultsContainer.innerHTML += `
                        <div class="col-lg-4 col-md-6 mb-6 animate-fadeInUp" style="animation-delay: ${delay}ms">
                            <div class="school-card bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden h-full">
                                <div class="h-48 bg-gradient-to-r from-blue-400 to-purple-500"></div>
                                <div class="p-6">
                                    <h5 class="text-xl font-bold mb-2">${school.name}</h5>
                                    <p class="text-gray-600 mb-3 flex items-center">
                                        <i class="fas fa-map-marker-alt mr-2 text-blue-500"></i>
                                        ${school.sector}, ${school.district}
                                    </p>
                                    <div class="flex flex-wrap gap-2 mb-4">
                                        <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                                            ${school.education_program}
                                        </span>
                                        <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                                            ${school.gender_policy}
                                        </span>
                                    </div>
                                    <div class="flex justify-between items-center">
                                        <span class="text-gray-700 font-medium">
                                            <i class="fas fa-city mr-1 text-purple-500"></i> 
                                            ${school.province}
                                        </span>
                                        <a href="/school/${school.id}" class="btn btn-sm btn-primary">
                                            View Details <i class="fas fa-arrow-right ml-1"></i>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
        });
}

// Helper function for recommendations
function performRecommendation() {
    const provinceInput = document.getElementById('recommend-province');
    const educationProgramInput = document.getElementById('recommend-education');
    const genderPolicyInput = document.getElementById('recommend-gender');
    const resultsContainer = document.getElementById('recommend-results');
    const recommendSection = document.getElementById('recommend');

    if (!provinceInput || !educationProgramInput || !genderPolicyInput || !resultsContainer || !recommendSection) {
        return;
    }

    const province = provinceInput.value;
    const educationProgram = educationProgramInput.value;
    const genderPolicy = genderPolicyInput.value;
    let url = '/recommend';
    const params = [];
    
    if (province) params.push(`province=${encodeURIComponent(province)}`);
    if (educationProgram) params.push(`education_program=${encodeURIComponent(educationProgram)}`);
    if (genderPolicy) params.push(`gender_policy=${encodeURIComponent(genderPolicy)}`);
    
    if (params.length > 0) url += `?${params.join('&')}`;
    
    // Show loading state
    resultsContainer.innerHTML = `
        <div class="col-12 text-center py-10">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-gray-600">Finding recommendations...</p>
        </div>
    `;
    
    // Scroll to results
    recommendSection.scrollIntoView({ behavior: 'smooth' });
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            resultsContainer.innerHTML = '';
            if (data.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="col-12 text-center py-10">
                        <i class="fas fa-graduation-cap text-gray-400 text-5xl mb-4"></i>
                        <h3 class="text-xl font-bold text-gray-700">No recommendations available</h3>
                        <p class="text-gray-500 mt-2">Try adjusting your criteria</p>
                    </div>
                `;
            } else {
                data.forEach((school, index) => {
                    // Add animation delay for staggered effect
                    const delay = index * 100;
                    resultsContainer.innerHTML += `
                        <div class="col-lg-4 col-md-6 mb-6 animate-fadeInUp" style="animation-delay: ${delay}ms">
                            <div class="school-card bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden h-full relative">
                                <div class="absolute top-3 left-3 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold z-10">
                                    RECOMMENDED
                                </div>
                                <div class="h-48 bg-gradient-to-r from-green-400 to-teal-500"></div>
                                <div class="p-6">
                                    <h5 class="text-xl font-bold mb-2">${school.name}</h5>
                                    <p class="text-gray-600 mb-3 flex items-center">
                                        <i class="fas fa-map-marker-alt mr-2 text-blue-500"></i>
                                        ${school.sector}, ${school.district}
                                    </p>
                                    <div class="flex flex-wrap gap-2 mb-4">
                                        <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                                            ${school.education_program}
                                        </span>
                                        <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                                            ${school.gender_policy}
                                        </span>
                                    </div>
                                    <div class="flex justify-between items-center">
                                        <span class="text-gray-700 font-medium">
                                            <i class="fas fa-city mr-1 text-purple-500"></i> 
                                            ${school.province}
                                        </span>
                                        <a href="/school/${school.id}" class="btn btn-sm btn-primary">
                                            View Details <i class="fas fa-arrow-right ml-1"></i>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
        });
}

// Add animations to school cards on scroll
document.addEventListener('DOMContentLoaded', function() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fadeInUp');
      }
    });
  }, { threshold: 0.1 });
  
  document.querySelectorAll('.school-card').forEach(card => {
    observer.observe(card);
  });
});
