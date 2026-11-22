package ir.noorhidayat.quran;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebView webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        webView.setBackgroundColor(0xFF101820);
        webView.loadUrl("file:///android_asset/index.html");
        setContentView(webView);
    }

    @Override
    public void onBackPressed() {
        WebView view = (WebView) findViewById(android.R.id.content).getRootView();
        super.onBackPressed();
    }
}
