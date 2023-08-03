# coding: utf-8

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from sqlalchemy.orm import relationship, backref

from sqlalchemy.ext.declarative import declarative_base

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


Base = declarative_base()

metadata = Base.metadata


class Product(db.Model):

    __tablename__ = 'product'

    id = Column(Integer, primary_key=True)

    product_name = Column(String(255), nullable=False)


class Location(db.Model):

    __tablename__ = 'location'

    id = Column(Integer, primary_key=True)

    product_id = Column(ForeignKey('product.id'), index=True)

    quantity = Column(Integer)

    location_name = Column(String(255))

    product = relationship('Product', backref=backref('locations', cascade='all, delete-orphan'))


class ProductMovement(db.Model):

    __tablename__ = 'product_movement'

    product_movement_id = Column(Integer, primary_key=True)

    product_id_fk = Column(ForeignKey('product.id'), index=True)

    from_location_id = Column(ForeignKey('location.id'), index=True)

    to_location_id = Column(ForeignKey('location.id'), index=True)

    quantity = Column(Integer)

    time_stamp = Column(DateTime)

    from_location = relationship(
        'Location', primaryjoin='ProductMovement.from_location_id == Location.id')

    product = relationship('Product')

    to_location = relationship(
        'Location', primaryjoin='ProductMovement.to_location_id == Location.id')
