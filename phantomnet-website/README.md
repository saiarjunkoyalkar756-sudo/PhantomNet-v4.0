# PhantomNet - Autonomous AI Cyber Defense Website

This is a next-level, enterprise-grade marketing website for PhantomNet, an AI-Driven Autonomous Cyber Defense Platform. It's built with modern web technologies to be performant, SEO-friendly, and deliver a premium user experience suitable for CISOs, security architects, enterprise buyers, and investors.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running Locally](#running-locally)
- [Deployment](#deployment)
- [Customization](#customization)
  - [Branding (Colors, Fonts)](#branding-colors-fonts)
  - [Content](#content)
  - [SEO Metadata](#seo-metadata)
  - [Animations](#animations)
- [Contributing](#contributing)
- [License](#license)

## Features

-   **Multi-Page Site:** Dedicated pages for Landing, Platform Overview, Architecture, AI & Intelligence, Features, Security & Trust, Demo/Roadmap, About/Vision, and Contact.
-   **Modern UI/UX:** Dark enterprise theme, minimalist design, high-contrast, professional typography.
-   **Smooth Animations:** Subtle, non-flashy animations powered by Framer Motion.
-   **Responsive Design:** Fully adaptive layouts for desktop, tablet, and mobile devices.
-   **SEO Optimized:** Server-side rendering (SSR), comprehensive meta tags, OpenGraph, and Twitter cards.
-   **SVG Visualizations:** Animated attack flow and interactive (conceptual) architecture diagrams.
-   **Reusable Components:** Modular and clean code structure.

## Tech Stack

-   **Frontend Framework:** [Next.js](https://nextjs.org/) (latest, App Router)
-   **Language:** [TypeScript](https://www.typescriptlang.org/)
-   **Styling:** [Tailwind CSS](https://tailwindcss.com/)
-   **Animations:** [Framer Motion](https://www.framer.com/motion/)
-   **UI Components:** [ShadCN UI](https://ui.shadcn.com/) (built on Radix UI and Tailwind CSS)
-   **Icons:** [Lucide Icons](https://lucide.dev/)
-   **Charting (Installed but not explicitly used in current pages):** [Recharts](https://recharts.org/en-US/)
-   **Utilities:** `clsx`, `tailwind-merge` for class management.

## Project Structure

```
phantomnet-website/
├── app/
│   ├── (marketing)/
│   │   ├── about/             # About / Vision Page
│   │   │   └── page.tsx
│   │   ├── ai-intelligence/   # AI & Intelligence Page
│   │   │   └── page.tsx
│   │   ├── architecture/      # Architecture Page
│   │   │   └── page.tsx
│   │   ├── contact/           # Contact / Request Demo Page
│   │   │   └── page.tsx
│   │   ├── features/          # Features Page
│   │   │   └── page.tsx
│   │   ├── platform/          # Platform Overview Page
│   │   │   └── page.tsx
│   │   ├── roadmap/           # Demo / Roadmap Page
│   │   │   └── page.tsx
│   │   └── page.tsx           # Home / Landing Page (root)
│   ├── globals.css            # Global Tailwind CSS and custom styles
│   └── layout.tsx             # Root layout with Header and Footer, global metadata
├── components/
│   ├── AnimatedAttackFlow.tsx # SVG component for animated attack flow
│   ├── ArchitectureDiagram.tsx # SVG component for architecture diagram
│   ├── Footer.tsx             # Global Footer component
│   └── Header.tsx             # Global Header/Navigation component
├── lib/
│   └── utils.ts               # ShadCN UI utility functions (cn for class merging)
├── public/                    # Static assets (images, favicon, etc.)
│   ├── favicon.ico
│   └── vercel.svg
├── tailwind.config.ts         # Tailwind CSS configuration
├── tsconfig.json              # TypeScript configuration
├── next.config.mjs            # Next.js configuration
├── package.json               # Project dependencies and scripts
└── README.md                  # This file
```

## Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

-   Node.js (v18.x or later)
-   npm (v8.x or later) or Yarn (v1.x or later) or pnpm (v8.x or later)

### Installation

1.  **Clone the repository (or navigate to the `phantomnet-website` directory):**
    ```bash
    git clone <repository-url> phantomnet-website
    cd phantomnet-website
    ```
    (If this project was generated for you, you are already in the correct directory.)

2.  **Install dependencies:**
    ```bash
    npm install
    # or yarn install
    # or pnpm install
    ```

### Running Locally

To run the development server:

```bash
npm run dev
# or yarn dev
# or pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
The page will auto-update as you edit the files.

## Deployment

This Next.js application can be easily deployed to various platforms.

-   **Vercel (Recommended):**
    The fastest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=appdir-template&filter=next.js&utm_source=create-next-app).
    You can deploy from your Git repository (GitHub, GitLab, Bitbucket).

-   **Other Platforms:**
    Refer to the [Next.js Deployment Documentation](https://nextjs.org/docs/deployment) for instructions on deploying to other platforms like Netlify, AWS Amplify, Docker, etc.

## Customization

### Branding (Colors, Fonts)

-   **Colors:**
    Customize the color palette by modifying `tailwind.config.ts` (look for `pn-` prefixed colors) and `app/globals.css` (the `:root` and `.dark` CSS variables).
    ```typescript
    // tailwind.config.ts
    // ...
    extend: {
        colors: {
            'pn-dark-blue': '#0D0D1A', // Base background
            'pn-neon-blue': '#00F0FF', // Primary accent
            'pn-electric-purple': '#8A2BE2', // Secondary accent
            // ...
        },
    }
    // ...
    ```
    ```css
    /* app/globals.css */
    :root {
      --pn-dark-blue: hsl(220 15% 5%);
      --pn-neon-blue: hsl(185 100% 50%);
      --pn-electric-purple: hsl(260 70% 60%);
      /* ... ensure these map to the tailwind config hex values converted to HSL */
    }
    .dark { /* ... same as :root for this dark theme */ }
    ```
-   **Fonts:**
    Change the primary (`--font-sans`) and heading (`--font-heading`) fonts.
    1.  Update the `@import url` in `app/globals.css` to link to your desired Google Fonts.
    2.  Modify the `Inter` and `Space_Grotesk` imports in `app/layout.tsx` to use your new font families from `next/font/google`.
    3.  Adjust `tailwind.config.ts`'s `fontFamily` section to reference your new fonts.

### Content

-   **Pages:** All page content resides in their respective `page.tsx` files under `app/(marketing)/`.
-   **Components:** Reusable components like `Header.tsx`, `Footer.tsx`, `AnimatedAttackFlow.tsx`, and `ArchitectureDiagram.tsx` are in the `components/` directory. Modify these to update structural elements or visualizations.

### SEO Metadata

Global SEO metadata is managed in `app/layout.tsx`. Update the `metadata` object for `title`, `description`, `keywords`, `openGraph`, and `twitter` properties.
For page-specific metadata, you can export a `metadata` object directly from each `page.tsx` file.

### Animations

Animations are primarily handled by [Framer Motion](https://www.framer.com/motion/). Review `motion` components and their `initial`, `animate`, `transition`, and `variants` props within page and component files to adjust animation behavior.

## Contributing

Please adhere to standard coding practices. Ensure your code is clean, well-commented (where necessary for complex logic), and follows the existing patterns.

## License

[MIT License](LICENSE) (placeholder, create a LICENSE file if needed)

---
*Generated by Gemini CLI*