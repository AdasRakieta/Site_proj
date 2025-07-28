// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "SmartHomeApp",
    platforms: [
        .iOS(.v14)
    ],
    products: [
        .library(
            name: "SmartHomeApp",
            targets: ["SmartHomeApp"]),
    ],
    dependencies: [
        // PostgreSQL support for iOS
        .package(url: "https://github.com/vapor/postgres-nio.git", from: "1.14.0"),
        // Networking support
        .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.8.0"),
    ],
    targets: [
        .target(
            name: "SmartHomeApp",
            dependencies: [
                .product(name: "PostgresNIO", package: "postgres-nio"),
                "Alamofire"
            ]),
        .testTarget(
            name: "SmartHomeAppTests",
            dependencies: ["SmartHomeApp"]),
    ]
)