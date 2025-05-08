document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const errorsDiv = document.getElementById('errors');
    const enhancedSection = document.getElementById('enhanced-section');
    const enhancedContent = document.getElementById('enhanced-content');

    async function performSearch(query) {
        if (!query.trim()) {
            return;
        }

        // Show loading, hide results and errors
        loadingDiv.style.display = 'block';
        resultsDiv.style.display = 'none';
        enhancedSection.style.display = 'none';
        errorsDiv.style.display = 'none';
        errorsDiv.textContent = '';

        try {
            const response = await fetch(`/search/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            // Hide loading
            loadingDiv.style.display = 'none';
            
            if (data.error) {
                // Show error message
                errorsDiv.textContent = data.error;
                errorsDiv.style.display = 'block';
                return;
            }

            // Display results
            displayResults(data);
            
        } catch (error) {
            // Hide loading, show error
            loadingDiv.style.display = 'none';
            errorsDiv.textContent = 'An error occurred while searching. Please try again.';
            errorsDiv.style.display = 'block';
            console.error('Search error:', error);
        }
    }

    // Function to display search results
    function displayResults(data) {
        resultsDiv.innerHTML = '';

        // Show enhanced content if available
        if (data.enhanced_response) {
            enhancedContent.innerHTML = formatAIResponse(data.enhanced_response);
            enhancedSection.style.display = 'block';
        }

        if (data.results && data.results.length > 0) {
            data.results.forEach(result => {
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                
                let highlightHTML = '';
                if (result.highlights && result.highlights.length > 0) {
                    highlightHTML = result.highlights.join('... ');
                } else {
                    // Show a snippet of the text if no highlights
                    highlightHTML = result.text.substring(0, 200) + '...';
                }

                resultItem.innerHTML = `
                    <div class="result-title">Document: ${result.doc_id}</div>
                    <div class="result-text">${highlightHTML}</div>
                `;
                
                resultsDiv.appendChild(resultItem);
            });
            
            resultsDiv.style.display = 'block';
        } else {
            resultsDiv.innerHTML = '<p>No results found for your query.</p>';
            resultsDiv.style.display = 'block';
        }
    }

    // Format AI response
    function formatAIResponse(text) {
        let formatted = text;
        
        // Convert newlines to <br>
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Convert numbered lists
        formatted = formatted.replace(/(\d+)\.\s(.*?)(?=<br>\d+\.|<br>$|$)/g, '<p><strong>$1.</strong> $2</p>');
        
        return formatted;
    }

    // Search button click event
    searchButton.addEventListener('click', function() {
        performSearch(searchInput.value);
    });

    // Enter key in search input
    searchInput.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            performSearch(searchInput.value);
        }
    });
}); 