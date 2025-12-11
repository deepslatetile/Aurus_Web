
async function loadPageContent() {
    try {
        const response = await fetch('/api/get/page_content/privacy-policy');

        if (!response.ok) {
            throw new Error('Failed to load page content');
        }

        const pageData = await response.json();

        document.getElementById('pageTitle').textContent = pageData.page_display || 'Privacy Policy';
        document.getElementById('lastUpdated').textContent = `Last updated: ${new Date(pageData.last_updated * 1000).toLocaleDateString()}`;

        const contentDiv = document.getElementById('pageContent');
        if (pageData.content) {
            contentDiv.innerHTML = pageData.content;
            contentDiv.classList.remove('content-loading');
        } else {
            console.error('Error loading page content:', error);
            const contentDiv = document.getElementById('pageContent');
            contentDiv.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <h3>Unable to Load Content</h3>
                    <p>We're having trouble loading the Privacy Policy. Please try again later.</p>
                    <a href="/" class="back-link">
                        <i class="fas fa-arrow-left"></i> Back to Home
                    </a>
                </div>
            `;
            contentDiv.classList.remove('content-loading');
        }

    } catch (error) {
        console.error('Error loading page content:', error);
        const contentDiv = document.getElementById('pageContent');
        contentDiv.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <h3>Unable to Load Content</h3>
                <p>We're having trouble loading the Privacy Policy. Please try again later.</p>
                <a href="/" class="back-link">
                    <i class="fas fa-arrow-left"></i> Back to Home
                </a>
            </div>
        `;
        contentDiv.classList.remove('content-loading');
    }
}

document.addEventListener('DOMContentLoaded', loadPageContent);
