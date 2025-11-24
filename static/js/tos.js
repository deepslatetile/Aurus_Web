async function loadPageContent() {
    try {
        const response = await fetch('/api/get/page_content/tos');

        if (!response.ok) {
            throw new Error('Failed to load page content');
        }

        const pageData = await response.json();

        // Update page title and metadata
        document.getElementById('pageTitle').textContent = pageData.page_display || 'Terms of Service';
        document.getElementById('lastUpdated').textContent = `Last updated: ${new Date(pageData.last_updated * 1000).toLocaleDateString()}`;

        // Update content
        const contentDiv = document.getElementById('pageContent');
        if (pageData.content) {
            contentDiv.innerHTML = pageData.content;
            contentDiv.classList.remove('content-loading');
        } else {
            contentDiv.innerHTML = `
                <div class="default-content">
                    <h2>Welcome to Aurus Airlines</h2>
                    <p>Our Terms of Service are currently being updated. Please check back soon for the complete terms and conditions.</p>

                    <h2>General Principles</h2>
                    <p>At Aurus Airlines, we are committed to providing exceptional service while maintaining the highest standards of safety and customer care.</p>

                    <h2>Contact Us</h2>
                    <p>If you have any questions about our terms of service, please contact our customer support team.</p>
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
                <p>We're having trouble loading the Terms of Service. Please try again later.</p>
                <a href="/" class="back-link">
                    <i class="fas fa-arrow-left"></i> Back to Home
                </a>
            </div>
        `;
        contentDiv.classList.remove('content-loading');
    }
}

document.addEventListener('DOMContentLoaded', loadPageContent);