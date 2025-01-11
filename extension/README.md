# Twitter Notification Tracker

## Functionality

When new replies appear, this extension will trigger a workflow that ensures a response to and/or a like on the incoming reply, depending on the context of that reply.

## Installation Instructions for Development Mode

To install the Twitter Notification Tracker extension in development mode, follow these steps:

1. **Open Chrome**:
   Launch the Google Chrome browser.

2. **Access Extensions Page**:
   Navigate to the Extensions page by entering `chrome://extensions/` in the address bar.

3. **Enable Developer Mode**:
   Toggle the "Developer mode" switch located in the top right corner of the Extensions page.

4. **Load Unpacked Extension**:
   Click on the "Load unpacked" button and select the directory where the extension files are located (the directory containing `manifest.json`).

5. **Test the Extension**:
   Once loaded, navigate to `https://x.com/notifications` to test the extension functionality.

6. **Debugging**:
   You can inspect the background page and content scripts using the Chrome Developer Tools (F12) to debug any issues.

7. **Make Changes**:
   If you make any changes to the extension code, simply refresh the Extensions page and click the refresh icon on the extension to apply the changes.

8. **Disable or Remove**:
   To disable or remove the extension, return to the Extensions page and toggle the switch or click the "Remove" button.

## Development Mode Tips

For development mode, it will be helpful to add a flag in localStorage: `twitter_extension_test_mode: true`. In this case, the extension will not check if a reply has been added to IndexedDB and will process all replies present in the notifications.
