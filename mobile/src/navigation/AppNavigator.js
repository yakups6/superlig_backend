import React from 'react';
import { View } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

import HomeScreen from '../screens/HomeScreen';
import FixturesScreen from '../screens/FixturesScreen';
import TeamAnalysisScreen from '../screens/TeamAnalysisScreen';
import TransfersScreen from '../screens/TransfersScreen';
import CompareScreen from '../screens/CompareScreen';
import ScoutScreen from '../screens/ScoutScreen';
import PlayersScreen from '../screens/PlayersScreen';
import StandingsScreen from '../screens/StandingsScreen';
import LegendsScreen from '../screens/LegendsScreen';
import AuthScreen from '../screens/AuthScreen';
import { COLORS } from '../theme/colors';

const Tab = createBottomTabNavigator();
const RootStack = createNativeStackNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: COLORS.dockBg,
          borderTopColor: COLORS.cardBorderStrong,
          borderTopWidth: 1,
          height: 64,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.textDim,
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '800',
        },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeScreen}
        options={{
          tabBarLabel: 'Ana Sayfa',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size - 2} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="FixturesTab"
        component={FixturesScreen}
        options={{
          tabBarLabel: 'Canlı Skor',
          tabBarIcon: ({ color, size }) => (
            <View>
              <Ionicons name="football" size={size - 2} color={color} />
              <View
                style={{
                  position: 'absolute',
                  top: -1,
                  right: -4,
                  width: 7,
                  height: 7,
                  borderRadius: 4,
                  backgroundColor: COLORS.accentRed,
                }}
              />
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="TeamsTab"
        component={TeamAnalysisScreen}
        options={{
          tabBarLabel: 'Takımlar',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="shield-half" size={size - 2} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="TransfersTab"
        component={TransfersScreen}
        options={{
          tabBarLabel: 'Transfer',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="swap-horizontal" size={size - 2} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="CompareTab"
        component={CompareScreen}
        options={{
          tabBarLabel: 'Karşılaştır',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="stats-chart" size={size - 2} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="ScoutTab"
        component={ScoutScreen}
        options={{
          tabBarLabel: 'Favoriler',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="heart" size={size - 2} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <RootStack.Navigator screenOptions={{ headerShown: false }}>
      <RootStack.Screen name="MainTabs" component={MainTabs} />
      <RootStack.Screen name="Players" component={PlayersScreen} />
      <RootStack.Screen name="Legends" component={LegendsScreen} />
      <RootStack.Screen name="Standings" component={StandingsScreen} />
      <RootStack.Screen name="Auth" component={AuthScreen} />
    </RootStack.Navigator>
  );
}
