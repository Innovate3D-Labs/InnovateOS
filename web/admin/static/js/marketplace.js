document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let allPlugins = [];
    let currentFilters = {
        category: '',
        search: ''
    };

    // Initialize marketplace
    initializeMarketplace();

    // Event listeners
    document.getElementById('searchPlugins').addEventListener('input', handleSearch);
    document.getElementById('categoryFilter').addEventListener('change', handleCategoryFilter);

    async function initializeMarketplace() {
        try {
            // Fetch plugins from server
            const response = await fetch('/api/plugins/marketplace');
            allPlugins = await response.json();

            // Display plugins
            displayFeaturedPlugins();
            filterAndDisplayPlugins();
        } catch (error) {
            console.error('Error initializing marketplace:', error);
            showError('Failed to load plugins');
        }
    }

    function displayFeaturedPlugins() {
        const featured = allPlugins.filter(plugin => plugin.featured);
        const container = document.getElementById('featuredPlugins');
        container.innerHTML = '';

        featured.forEach(plugin => {
            const card = createPluginCard(plugin, true);
            container.appendChild(card);
        });
    }

    function filterAndDisplayPlugins() {
        let filtered = allPlugins;

        // Apply category filter
        if (currentFilters.category) {
            filtered = filtered.filter(plugin => 
                plugin.category === currentFilters.category
            );
        }

        // Apply search filter
        if (currentFilters.search) {
            const searchTerm = currentFilters.search.toLowerCase();
            filtered = filtered.filter(plugin =>
                plugin.name.toLowerCase().includes(searchTerm) ||
                plugin.description.toLowerCase().includes(searchTerm)
            );
        }

        displayPlugins(filtered);
    }

    function displayPlugins(plugins) {
        const grid = document.getElementById('pluginGrid');
        grid.innerHTML = '';

        plugins.forEach(plugin => {
            const card = createPluginCard(plugin);
            grid.appendChild(card);
        });
    }

    function createPluginCard(plugin, isFeatured = false) {
        const template = document.getElementById('pluginCardTemplate');
        const card = template.content.cloneNode(true);

        // Fill in plugin details
        card.querySelector('.plugin-thumbnail').src = plugin.thumbnail_url;
        card.querySelector('.plugin-name').textContent = plugin.name;
        card.querySelector('.plugin-description').textContent = plugin.description;
        card.querySelector('.plugin-version').textContent = `v${plugin.version}`;
        card.querySelector('.plugin-downloads').textContent = 
            `${plugin.downloads} downloads`;

        // Add event listeners
        card.querySelector('.view-details').addEventListener('click', () => 
            showPluginDetails(plugin)
        );
        card.querySelector('.install-plugin').addEventListener('click', () => 
            installPlugin(plugin)
        );

        if (isFeatured) {
            card.querySelector('.card').classList.add('border-primary');
        }

        return card;
    }

    async function showPluginDetails(plugin) {
        const modal = document.getElementById('pluginModal');
        const modalBody = modal.querySelector('.modal-body');

        try {
            // Fetch detailed plugin information
            const response = await fetch(`/api/plugins/marketplace/${plugin.id}`);
            const details = await response.json();

            // Update modal content
            modalBody.innerHTML = `
                <div class="row">
                    <div class="col-md-4">
                        <img src="${details.thumbnail_url}" class="img-fluid" alt="${details.name}">
                    </div>
                    <div class="col-md-8">
                        <h4>${details.name}</h4>
                        <p>${details.description}</p>
                        <hr>
                        <dl>
                            <dt>Version</dt>
                            <dd>${details.version}</dd>
                            <dt>Author</dt>
                            <dd>${details.author}</dd>
                            <dt>Downloads</dt>
                            <dd>${details.downloads}</dd>
                            <dt>Last Updated</dt>
                            <dd>${new Date(details.last_updated).toLocaleDateString()}</dd>
                        </dl>
                    </div>
                </div>
                <div class="mt-3">
                    <h5>Features</h5>
                    <ul>
                        ${details.features.map(f => `<li>${f}</li>`).join('')}
                    </ul>
                </div>
            `;

            // Show modal
            new bootstrap.Modal(modal).show();
        } catch (error) {
            console.error('Error fetching plugin details:', error);
            showError('Failed to load plugin details');
        }
    }

    async function installPlugin(plugin) {
        try {
            const response = await fetch('/api/plugins/install', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    plugin_id: plugin.id,
                    version: plugin.version
                })
            });

            if (!response.ok) throw new Error('Installation failed');

            showSuccess(`Successfully installed ${plugin.name}`);
        } catch (error) {
            console.error('Error installing plugin:', error);
            showError('Failed to install plugin');
        }
    }

    function handleSearch(event) {
        currentFilters.search = event.target.value;
        filterAndDisplayPlugins();
    }

    function handleCategoryFilter(event) {
        currentFilters.category = event.target.value;
        filterAndDisplayPlugins();
    }

    function showError(message) {
        // Implementation of error toast notification
    }

    function showSuccess(message) {
        // Implementation of success toast notification
    }
});
