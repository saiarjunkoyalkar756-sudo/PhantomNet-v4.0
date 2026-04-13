// script.js

document.addEventListener('DOMContentLoaded', () => {
    const navSlide = () => {
        const burger = document.querySelector('.burger');
        const nav = document.querySelector('.nav-links');
        const navLinks = document.querySelectorAll('.nav-links li');

        // Toggle Nav
        burger.addEventListener('click', () => {
            nav.classList.toggle('nav-active');

            // Animate Links
            navLinks.forEach((link, index) => {
                if (link.style.animation) {
                    link.style.animation = '';
                } else {
                    link.style.animation = `navLinkFade 0.5s ease forwards ${index / 7 + 0.5}s`;
                }
            });

            // Burger Animation
            burger.classList.toggle('toggle');
        });

        // Close nav when a link is clicked (for single page navigation)
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (nav.classList.contains('nav-active')) {
                    nav.classList.remove('nav-active');
                    burger.classList.remove('toggle');
                    navLinks.forEach(item => {
                        item.style.animation = ''; // Reset animation
                    });
                }
            });
        });
    }

    // Call the navSlide function
    navSlide();

    // Simple scroll-based animation for sections
    const sections = document.querySelectorAll('.section, .demo-cta-section');

    const fadeIn = (element) => {
        element.style.opacity = 1;
        element.style.transform = 'translateY(0)';
    };

    const handleScroll = () => {
        sections.forEach(section => {
            const sectionTop = section.getBoundingClientRect().top;
            const screenHeight = window.innerHeight;

            if (sectionTop < screenHeight * 0.75) { // When 25% of the section is visible
                fadeIn(section);
            }
        });
    };

    // Initialize sections to be invisible and slightly offset
    sections.forEach(section => {
        section.style.opacity = 0;
        section.style.transform = 'translateY(50px)';
        section.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
    });

    // Check on load and scroll
    handleScroll(); // Check immediately on load for elements already in view
    window.addEventListener('scroll', handleScroll);
});

/* Keyframe for nav link fade-in */
const styleSheet = document.styleSheets[0];
const navLinkFadeKeyframes = `
@keyframes navLinkFade {
    from {
        opacity: 0;
        transform: translateX(50px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}
`;
styleSheet.insertRule(navLinkFadeKeyframes, styleSheet.cssRules.length);
