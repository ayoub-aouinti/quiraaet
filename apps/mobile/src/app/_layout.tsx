import { AmiriQuran_400Regular, useFonts } from '@expo-google-fonts/amiri-quran';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { color } from '@jamei/shared';
import { MetaProvider } from '../lib/meta';

export default function RootLayout() {
  // الخطُّ القرآنيُّ يُحمَّل في الخلفية، والنصُّ يظهر بخطِّ النظام إلى أن يصل.
  useFonts({ AmiriQuran_400Regular });
  return (
    <MetaProvider>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: color.paper },
          headerTintColor: color.ink,
          headerTitleStyle: { fontWeight: '600' },
          contentStyle: { backgroundColor: color.leaf },
          headerBackButtonDisplayMode: 'minimal',
        }}
      >
        <Stack.Screen name="index" options={{ title: 'جامع الوقوف' }} />
        <Stack.Screen name="sura/[id]" options={{ title: '' }} />
        <Stack.Screen name="word/[seq]" options={{ title: 'تفصيل الموضع', presentation: 'modal' }} />
        <Stack.Screen name="sources" options={{ title: 'المصادر' }} />
        <Stack.Screen name="search" options={{ title: 'البحث' }} />
      </Stack>
    </MetaProvider>
  );
}
