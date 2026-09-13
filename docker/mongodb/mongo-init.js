// mongo-init.js
// Auto-generated initial database provisioning for Dedisalam platform

const userDb = db.getSiblingDB('user_db');
userDb.createCollection('users');

const superAdminExists = userDb.users.findOne({
  $or: [{ email: 'superadmin@example.com' }, { role: 'super_admin' }]
});

if (!superAdminExists) {
  userDb.users.insertOne({
    email: 'superadmin@example.com',
    password: '$2b$10$I.VeClX0Khrd.GRlxM.ntOOf6C278AnxXKrq8PgOMw/CwGNG4ZRxS', // Admin123!
    name: 'Super Administrator',
    role: 'super_admin',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date()
  });
}

const notificationDb = db.getSiblingDB('notification_db');
notificationDb.createCollection('notifications');
