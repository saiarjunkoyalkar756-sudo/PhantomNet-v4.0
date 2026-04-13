### Environment Variables for Production

Create a file named `.env.production` in the root of your project. This file will be used for production builds. It should contain the URL of your production API.

**.env.production**
```
VITE_API_URL=https://your-production-api.com/api
```

### Local Development Environment

For local development, you can use the `.env` file.

**.env**
```
VITE_API_URL=http://localhost:3001/api
```

---

### How to Test the Production Build Locally

1.  **Build the Project:**
    This command will create a `dist` folder with the optimized production build.
    ```bash
    npm run build
    ```

2.  **Preview the Production Build:**
    This command will start a local static web server that serves the files from the `dist` folder.
    ```bash
    npm run preview
    ```
    The application will be available at the URL provided by the preview server (usually `http://localhost:4173`).

3.  **Open Browser and Developer Console:**
    Open your web browser and navigate to the preview URL. Open the developer console (F12) and check for any errors in the 'Console' tab.

4.  **Verify Network Requests:**
    In the developer console, switch to the 'Network' tab. When you try to log in, you should see a network request to the `VITE_API_URL` you have configured. Verify that the request is successful and that you are receiving the expected data.

5.  **Check Routing:**
    Test the different routes of your application to ensure that the router is working correctly. Try accessing a protected route without being logged in, and verify that you are redirected to the login page. Try accessing an admin-only route as a regular user, and verify that you are redirected.

By following these steps, you should be able to identify and debug any issues with your production build.
