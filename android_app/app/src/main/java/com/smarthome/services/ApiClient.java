package com.smarthome.services;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKeys;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.IOException;
import java.security.GeneralSecurityException;
import java.util.concurrent.TimeUnit;

import okhttp3.Cookie;
import okhttp3.CookieJar;
import okhttp3.HttpUrl;
import okhttp3.Interceptor;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class ApiClient {
    private static final String PREFERENCES_FILE = "smart_home_prefs";
    private static final String KEY_SERVER_URL = "server_url";
    private static final String KEY_SESSION_COOKIE = "session_cookie";
    
    private static ApiClient instance;
    private SmartHomeApiService apiService;
    private SharedPreferences preferences;
    private Context context;
    private String baseUrl;
    
    private ApiClient(Context context) {
        this.context = context.getApplicationContext();
        initializePreferences();
        initializeApiService();
    }
    
    public static synchronized ApiClient getInstance(Context context) {
        if (instance == null) {
            instance = new ApiClient(context);
        }
        return instance;
    }
    
    private void initializePreferences() {
        try {
            String masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC);
            preferences = EncryptedSharedPreferences.create(
                PREFERENCES_FILE,
                masterKeyAlias,
                context,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            );
        } catch (GeneralSecurityException | IOException e) {
            // Fallback to regular SharedPreferences if encryption fails
            preferences = context.getSharedPreferences(PREFERENCES_FILE, Context.MODE_PRIVATE);
        }
    }
    
    private void initializeApiService() {
        baseUrl = getServerUrl();
        if (baseUrl == null || baseUrl.isEmpty()) {
            baseUrl = "http://100.103.184.90:5000/"; // Default URL zmieniony na IP maliny
        }
        // Automatycznie dodaj schemat http:// jeśli użytkownik podał tylko IP lub adres bez schematu
        if (!baseUrl.startsWith("http://") && !baseUrl.startsWith("https://")) {
            baseUrl = "http://" + baseUrl;
        }
        // Ensure URL ends with /
        if (!baseUrl.endsWith("/")) {
            baseUrl += "/";
        }
        
        // Create cookie jar for session management
        CookieJar cookieJar = new CookieJar() {
            private final HashMap<String, List<Cookie>> cookieStore = new HashMap<>();
            
            @Override
            public void saveFromResponse(HttpUrl url, List<Cookie> cookies) {
                cookieStore.put(url.host(), cookies);
                // Save session cookie to preferences
                for (Cookie cookie : cookies) {
                    if ("session".equals(cookie.name())) {
                        saveSessionCookie(cookie.value());
                    }
                }
            }
            
            @Override
            public List<Cookie> loadForRequest(HttpUrl url) {
                List<Cookie> cookies = cookieStore.get(url.host());
                return cookies != null ? cookies : new ArrayList<>();
            }
        };
        
        // Create HTTP client with logging and session handling
        HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
        logging.setLevel(HttpLoggingInterceptor.Level.BODY);
        
        OkHttpClient client = new OkHttpClient.Builder()
            .addInterceptor(logging)
            .addInterceptor(new SessionInterceptor())
            .cookieJar(cookieJar)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build();
        
        // Create Gson with custom date format
        Gson gson = new GsonBuilder()
            .setDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS")
            .create();
        
        // Create Retrofit instance
        Retrofit retrofit = new Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build();
        
        apiService = retrofit.create(SmartHomeApiService.class);
    }
    
    public SmartHomeApiService getApiService() {
        return apiService;
    }
    
    public void setServerUrl(String url) {
        preferences.edit().putString(KEY_SERVER_URL, url).apply();
        baseUrl = url;
        initializeApiService(); // Reinitialize with new URL
    }
    
    public String getServerUrl() {
        return preferences.getString(KEY_SERVER_URL, "http://192.168.1.100:5000/");
    }
    
    public void saveSessionCookie(String sessionCookie) {
        preferences.edit().putString(KEY_SESSION_COOKIE, sessionCookie).apply();
    }
    
    public String getSessionCookie() {
        return preferences.getString(KEY_SESSION_COOKIE, null);
    }
    
    public void clearSession() {
        preferences.edit().remove(KEY_SESSION_COOKIE).apply();
    }
    
    // Interceptor to add session cookie to requests
    private class SessionInterceptor implements Interceptor {
        @Override
        public Response intercept(Chain chain) throws IOException {
            Request original = chain.request();
            Request.Builder requestBuilder = original.newBuilder();
            
            String sessionCookie = getSessionCookie();
            if (sessionCookie != null) {
                requestBuilder.addHeader("Cookie", "session=" + sessionCookie);
            }
            
            return chain.proceed(requestBuilder.build());
        }
    }
}