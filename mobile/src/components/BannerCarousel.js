import React from 'react';
import { View, ScrollView, Image, Dimensions, StyleSheet, TouchableOpacity, Linking } from 'react-native';
import { Colors } from '../constants/Colors';

const { width } = Dimensions.get('window');

const BannerCarousel = ({ banners }) => {
  if (!banners || banners.length === 0) return null;

  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {banners.map((banner, index) => (
          <TouchableOpacity
            key={index}
            activeOpacity={0.9}
            onPress={() => banner.url && Linking.openURL(banner.url)}
          >
            <Image
              source={{ uri: banner.image }}
              style={styles.image}
            />
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: 180,
    marginVertical: 15,
  },
  scrollContent: {
    paddingHorizontal: 10,
  },
  image: {
    width: width - 40,
    height: 180,
    borderRadius: 15,
    marginHorizontal: 10,
    backgroundColor: Colors.card,
  },
});

export default BannerCarousel;
