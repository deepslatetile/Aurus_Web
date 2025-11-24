async function loadPageContent() {
    try {
        const response = await fetch('/api/get/page_content/privacy-policy');

        if (!response.ok) {
            throw new Error('Failed to load page content');
        }

        const pageData = await response.json();

        // Update page title and metadata
        document.getElementById('pageTitle').textContent = pageData.page_display || 'Privacy Policy';
        document.getElementById('lastUpdated').textContent = `Last updated: ${new Date(pageData.last_updated * 1000).toLocaleDateString()}`;

        // Update content
        const contentDiv = document.getElementById('pageContent');
        if (pageData.content) {
            contentDiv.innerHTML = pageData.content;
            contentDiv.classList.remove('content-loading');
        } else {
            contentDiv.innerHTML = `
                <div class="default-content">
                    <div class="privacy-highlight">
                        <p><strong>Your privacy is important to us.</strong> This privacy policy outlines how Aurus Airlines collects, uses, and protects your personal information.</p>
                    </div>

                    <h2>Information We Collect</h2>
                    <p>We collect information that you provide directly to us, including:</p>
                    <ul>
                        <li>Personal identification information</li>
                        <li>Flight booking details</li>
                        <li>Payment information</li>
                        <li>Communication preferences</li>
                    </ul>

                    <h2>How We Use Your Information</h2>
                    <p>Your information helps us provide and improve our services, including:</p>
                    <ul>
                        <li>Processing your bookings and payments</li>
                        <li>Personalizing your experience</li>
                        <li>Communicating important updates</li>
                        <li>Ensuring flight safety and security</li>
                    </ul>

                    <h2>Data Protection</h2>
                    <p>We implement appropriate security measures to protect your personal information from unauthorized access, alteration, or disclosure.</p>

                    <h2>Contact Us</h2>
                    <p>For questions about our privacy practices, please contact our privacy team.</p>
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