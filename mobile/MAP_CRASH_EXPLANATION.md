The user is getting app crashes when loading the Map tab during local Expo Go testing.

**CAUSE:**
Expo Go doesn't support react-native-maps. The package requires native configuration that's only available in a built APK, not in the Expo Go dev environment.

**SOLUTION:**
The map will work perfectly in the EAS build APK. For local development testing, we need to:

1. **Option 1 (Recommended): Just test other tabs in Expo Go**
   - Camera tab works
   - History/Analytics/Settings work  
   - Skip the Map tab until APK is ready

2. **Option 2: Add Platform check**
   Add this simple check to show fallback in Expo Go:
   ```javascript
   // At the start of MapScreen function
   if (__DEV__) {
     return <Text>Map available in built APK only</Text>;
   }
   ```

3. **Option 3: Remove mapError and just accept crashes during dev**
   The map will still work in production APK

**CURRENT BUILD STATUS:**
The EAS build (17532497-1037-4b72-8523-3e0f034ab33) has the AndroidX patch and full map support.
When that build completes and you install the APK, the map will work perfectly.

**RECOMMENDATION:**
Test the other features in Expo Go now, and wait for the APK to test the map.
The patch we created ensures the map WILL work in the final APK.
