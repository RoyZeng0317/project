package com.example.nfu

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            "nfu/navigation",
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "openNavigation" -> {
                    val latitude = call.argument<Double>("latitude")
                    val longitude = call.argument<Double>("longitude")

                    if (latitude == null || longitude == null) {
                        result.error(
                            "INVALID_DESTINATION",
                            "Navigation destination is missing.",
                            null,
                        )
                        return@setMethodCallHandler
                    }

                    openGoogleMapsNavigation(latitude, longitude, result)
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun openGoogleMapsNavigation(
        latitude: Double,
        longitude: Double,
        result: MethodChannel.Result,
    ) {
        val navigationUri = Uri.parse("google.navigation:q=$latitude,$longitude&mode=d")
        val intent = Intent(Intent.ACTION_VIEW, navigationUri).apply {
            setPackage("com.google.android.apps.maps")
        }

        try {
            startActivity(intent)
            result.success(null)
        } catch (_: ActivityNotFoundException) {
            val fallbackUri = Uri.parse(
                "https://www.google.com/maps/dir/?api=1&destination=$latitude,$longitude&travelmode=driving",
            )
            val fallbackIntent = Intent(Intent.ACTION_VIEW, fallbackUri)

            try {
                startActivity(fallbackIntent)
                result.success(null)
            } catch (_: ActivityNotFoundException) {
                result.error("NO_MAPS_APP", "No app can open Google Maps navigation.", null)
            }
        }
    }
}
